"""Run a real local model against Google Sheets or a connected-tool bridge."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from relayops.agent import BridgeTransport, OllamaPlanner, WorkspaceTools, run_agent
from relayops.connectors import GoogleSheets

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
parser.add_argument("--spreadsheet-id", required=True)
parser.add_argument("--trace", required=True)
parser.add_argument("--bridge-dir")
parser.add_argument("--confirm-write", action="store_true")
parser.add_argument(
    "--objective",
    default="Revise os leads novos, registre a análise e a próxima ação no CRM, sinalize conflitos e confira cada gravação. Não envie mensagens.",
)
args = parser.parse_args()
if not args.confirm_write:
    parser.error(
        "Requires --confirm-write to update AgentReview rows in the selected sandbox"
    )
if args.bridge_dir:
    connector = GoogleSheets(
        args.spreadsheet_id,
        "bridge-no-credential",
        BridgeTransport(args.bridge_dir, timeout=600),
    )
else:
    connector = GoogleSheets(args.spreadsheet_id, os.environ["GOOGLE_ACCESS_TOKEN"])
print(
    json.dumps(
        run_agent(
            args.objective,
            OllamaPlanner(args.model),
            WorkspaceTools(connector),
            args.trace,
        ),
        ensure_ascii=False,
    )
)
