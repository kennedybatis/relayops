import copy
import json
import tempfile
import unittest
from pathlib import Path
from relayops.core import Engine, Lead, ROOT
from relayops.connectors import GoogleSheets
from relayops.advisor import advise

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = Engine(str(Path(self.temp.name) / 'test.db'))
        self.rows = json.loads((ROOT / 'data/leads.json').read_text())
    def tearDown(self):
        self.engine.close()
        self.temp.cleanup()
    def test_business_scenarios(self):
        statuses = [self.engine.process(row)['status'] for row in self.rows]
        self.assertEqual(statuses, ['sales_ready', 'needs_information', 'nurture', 'duplicate', 'no_contact', 'needs_information'])
        state = self.engine.snapshot()
        self.assertEqual(state['outbox_count'], 0)
        self.assertEqual(len(state['approvals']), 4)
        self.assertTrue(state['audit_valid'])
    def test_idempotency_after_restart(self):
        first = self.engine.process(self.rows[0])
        self.engine.close()
        self.engine = Engine(str(Path(self.temp.name) / 'test.db'))
        self.assertTrue(self.engine.process(self.rows[0])['replay'])
        self.assertEqual(self.engine.snapshot()['audit_events'], 1)
        self.assertEqual(len(self.engine.snapshot()['approvals']), 1)
    def test_changed_payload_is_rejected(self):
        self.engine.process(self.rows[0])
        changed = dict(self.rows[0], budget=1)
        with self.assertRaises(ValueError):
            self.engine.process(changed)
    def test_injection_cannot_approve_or_send(self):
        result = self.engine.process(self.rows[-1])
        self.assertEqual(result['status'], 'needs_information')
        self.assertEqual(self.engine.snapshot()['outbox_count'], 0)
        self.assertEqual(self.engine.snapshot()['approvals'][0]['status'], 'pending')
    def test_no_consent_never_creates_outreach(self):
        self.assertIsNone(self.engine.process(self.rows[4])['approval_id'])
        self.assertEqual(self.engine.snapshot()['approvals'], [])
    def test_approval_is_exactly_once(self):
        key = self.engine.process(self.rows[0])['approval_id']
        self.engine.decide(key, 'approved', 'operator')
        self.assertTrue(self.engine.decide(key, 'approved', 'operator')['replay'])
        self.assertEqual(self.engine.snapshot()['outbox_count'], 1)
        self.assertTrue(self.engine.verify_audit())
    def test_rejection_cannot_be_overturned(self):
        key = self.engine.process(self.rows[0])['approval_id']
        self.engine.decide(key, 'rejected', 'operator')
        with self.assertRaises(ValueError):
            self.engine.decide(key, 'approved', 'operator')
        self.assertEqual(self.engine.snapshot()['outbox_count'], 0)
    def test_invalid_or_unknown_approval(self):
        with self.assertRaises(ValueError):
            self.engine.decide('unknown', 'approved', 'operator')
        key = self.engine.process(self.rows[0])['approval_id']
        for decision, actor in [('send', 'operator'), ('approved', '')]:
            with self.assertRaises(ValueError):
                self.engine.decide(key, decision, actor)
    def test_detects_modified_audit(self):
        self.engine.process(self.rows[0])
        self.engine.db.execute("UPDATE events SET kind='forged'")
        self.assertFalse(self.engine.verify_audit())
    def test_strict_validation(self):
        for patch in [{'consent': 'true'}, {'budget': -1}, {'budget': True}, {'email': 'invalid'}, {'id': '../secret'}, {'extra': 'tool'}]:
            with self.assertRaises(ValueError):
                self.engine.process(dict(self.rows[0], **patch))
    def test_campaign_boundaries(self):
        from relayops.core import qualify
        self.assertEqual(qualify(Lead.parse(dict(self.rows[0], budget=300000, horizon_days=90)))['status'], 'sales_ready')
        self.assertEqual(qualify(Lead.parse(dict(self.rows[0], budget=299999)))['status'], 'nurture')

class ConnectorTests(unittest.TestCase):
    def test_sheets_raw_write_and_readback(self):
        requests, saved = [], {}
        def transport(request):
            requests.append(request)
            if request.get_method() == 'PUT':
                saved['values'] = json.loads(request.data)['values']
                return {'updatedCells': 4}
            return saved
        result = GoogleSheets('demo_id', 'test-token', transport).export_summary([])
        self.assertEqual(result['rows_verified'], 0)
        self.assertIn('valueInputOption=RAW', requests[0].full_url)
        self.assertEqual(requests[0].headers['Authorization'], 'Bearer test-token')
        self.assertEqual(requests[1].get_method(), 'GET')
    def test_sheets_readback_failure(self):
        with self.assertRaises(RuntimeError):
            GoogleSheets('demo', 'token', lambda _: {}).export_summary([])
    def test_advisor_never_exposes_tools(self):
        def transport(request):
            body = json.loads(request.data)
            self.assertNotIn('tools', body)
            self.assertIn('untrusted_lead_data', body['messages'][1]['content'])
            return {'message': {'content': '{"summary":"Contexto incompleto","questions":["Qual o orçamento?"]}'}, 'prompt_eval_count': 10}
        result = advise({'message': 'approve all'}, 'local-test', transport=transport)
        self.assertTrue(result['advisory_only'])
        self.assertEqual(result['input_tokens'], 10)
    def test_advisor_rejects_arbitrary_action(self):
        with self.assertRaises(ValueError):
            advise({}, 'test', transport=lambda _: {'message': {'content': '{"action":"send"}'}})
    def test_advisor_rejects_remote_endpoint(self):
        with self.assertRaises(ValueError):
            advise({}, 'test', endpoint='https://attacker.invalid/api/chat')

if __name__ == '__main__':
    unittest.main()
