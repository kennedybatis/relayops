import argparse
import json
import os
from .core import Engine, ROOT

def main():
    parser = argparse.ArgumentParser(description='RelayOps — commercial agent reference')
    parser.add_argument('--db', default='runtime/relayops.db')
    sub = parser.add_subparsers(dest='command', required=True)
    for cmd in ('demo', 'report', 'serve'):
        sub.add_parser(cmd)
    decision = sub.add_parser('decide')
    decision.add_argument('id')
    decision.add_argument('decision', choices=['approved', 'rejected'])
    decision.add_argument('--actor', required=True)
    export = sub.add_parser('export-sheets')
    export.add_argument('--confirm-write', action='store_true')
    advice = sub.add_parser('advise')
    advice.add_argument('--model', required=True)
    args = parser.parse_args()
    if args.command == 'serve':
        from .server import serve
        serve(args.db)
        return
    engine = Engine(args.db)
    try:
        if args.command == 'demo':
            result = [engine.process(row) for row in json.loads((ROOT / 'data/leads.json').read_text())]
        elif args.command == 'report':
            result = engine.snapshot()
        elif args.command == 'decide':
            result = engine.decide(args.id, args.decision, args.actor)
        elif args.command == 'export-sheets':
            if not args.confirm_write:
                parser.error('Requires --confirm-write; this overwrites the RelayOps report tab')
            from .connectors import GoogleSheets
            result = GoogleSheets(os.environ['SHEETS_ID'], os.environ['GOOGLE_ACCESS_TOKEN']).export_summary(engine.snapshot()['runs'])
        else:
            from .advisor import advise
            result = advise(json.loads((ROOT / 'data/leads.json').read_text())[0], args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        engine.close()

if __name__ == '__main__':
    main()
