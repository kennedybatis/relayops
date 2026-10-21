"""Execution boundary: model output never grants permission."""
import hashlib
import json
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class Lead:
    id: str
    name: str
    email: str
    budget: int
    horizon_days: int
    consent: bool
    message: str = ''

    @classmethod
    def parse(cls, row):
        if set(row) != set(cls.__annotations__):
            raise ValueError('Unexpected or missing lead fields')
        for key in ('id', 'name', 'email', 'message'):
            if not isinstance(row[key], str) or len(row[key]) > 4000:
                raise ValueError('Invalid text field')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', row['id']):
            raise ValueError('Invalid lead id')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', row['email']):
            raise ValueError('Invalid email')
        for key in ('budget', 'horizon_days'):
            if type(row[key]) is not int or not 0 <= row[key] <= 10**9:
                raise ValueError('Invalid numeric field')
        if type(row['consent']) is not bool:
            raise ValueError('Consent must be a boolean')
        return cls(**row)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def qualify(lead):
    missing = [k for k in ('budget', 'horizon_days') if getattr(lead, k) == 0]
    if not lead.consent:
        return {'status': 'no_contact', 'reason': 'No permission for outreach', 'missing': missing}
    if missing:
        return {'status': 'needs_information', 'reason': 'Missing business context', 'missing': missing}
    ready = lead.budget >= 300000 and lead.horizon_days <= 90
    return {'status': 'sales_ready' if ready else 'nurture', 'reason': 'Budget and timeline match' if ready else 'Outside campaign criteria', 'missing': []}

class Engine:
    def __init__(self, path='runtime/relayops.db'):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=20)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, result TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS contacts(email TEXT PRIMARY KEY, lead_id TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL,
        reference TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL);
        ''')
    def close(self):
        self.db.close()
    def _event(self, kind, reference):
        last = self.db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        previous = last[0] if last else '0' * 64
        at = time.time()
        self.db.execute('INSERT INTO events(at,kind,reference,previous,hash) VALUES(?,?,?,?,?)',
                        (at, kind, reference, previous, digest([at, kind, reference, previous])))
    def process(self, raw):
        lead = Lead.parse(raw)
        key = digest(asdict(lead))
        started = time.perf_counter()
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            prior = self.db.execute('SELECT result FROM runs WHERE id=?', (lead.id,)).fetchone()
            if prior:
                result = json.loads(prior[0])
                if result['input_hash'] != key:
                    raise ValueError('Lead ID reused with changed payload; use a versioned ID')
                return dict(result, replay=True)
            known = self.db.execute('SELECT lead_id FROM contacts WHERE email=?', (lead.email.strip().lower(),)).fetchone()
            assessment = qualify(lead)
            if known:
                assessment = {'status': 'duplicate', 'reason': 'Email already exists', 'missing': []}
            result = {'id': lead.id, 'name': lead.name, 'input_hash': key, **assessment,
                      'approval_id': None, 'replay': False, 'mode': 'deterministic', 'model_tokens': 0,
                      'provider_cost_usd': 0, 'elapsed_ms': round((time.perf_counter() - started) * 1000, 3)}
            if assessment['status'] in ('sales_ready', 'needs_information', 'nurture'):
                payload = {'lead_id': lead.id, 'to': lead.email,
                           'body': 'Olá! Podemos confirmar seu orçamento e prazo para indicar o próximo passo?'}
                approval_id = digest(payload)[:24]
                self.db.execute('INSERT INTO approvals VALUES(?,?,?)', (approval_id, json.dumps(payload, ensure_ascii=False), 'pending'))
                result['approval_id'] = approval_id
            if not known:
                self.db.execute('INSERT INTO contacts VALUES(?,?)', (lead.email.strip().lower(), lead.id))
            self.db.execute('INSERT INTO runs VALUES(?,?)', (lead.id, json.dumps(result, ensure_ascii=False)))
            self._event('lead_processed', digest({'id': lead.id, 'result': result}))
        return result
    def decide(self, approval_id, decision, actor):
        if decision not in ('approved', 'rejected') or not isinstance(actor, str) or not actor.strip():
            raise ValueError('Decision and human actor required')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            item = self.db.execute('SELECT * FROM approvals WHERE id=?', (approval_id,)).fetchone()
            if item is None:
                raise ValueError('Unknown approval')
            if item['status'] != 'pending':
                if item['status'] != decision:
                    raise ValueError('Decision is final')
                return {'id': approval_id, 'status': decision, 'replay': True}
            self.db.execute('UPDATE approvals SET status=? WHERE id=?', (decision, approval_id))
            if decision == 'approved':
                self.db.execute('INSERT INTO outbox VALUES(?,?)', (approval_id, item['payload']))
            self._event('human_' + decision, digest({'id': approval_id, 'actor': actor.strip()}))
        return {'id': approval_id, 'status': decision, 'replay': False}
    def snapshot(self):
        return {'runs': [json.loads(r[0]) for r in self.db.execute('SELECT result FROM runs ORDER BY rowid')],
                'approvals': [{'id': r['id'], 'status': r['status'], 'payload': json.loads(r['payload'])} for r in self.db.execute('SELECT * FROM approvals')],
                'outbox_count': self.db.execute('SELECT count(*) FROM outbox').fetchone()[0],
                'audit_valid': self.verify_audit(), 'audit_events': self.db.execute('SELECT count(*) FROM events').fetchone()[0]}
    def verify_audit(self):
        previous = '0' * 64
        for row in self.db.execute('SELECT * FROM events ORDER BY seq'):
            if row['previous'] != previous or row['hash'] != digest([row['at'], row['kind'], row['reference'], previous]):
                return False
            previous = row['hash']
        return True
