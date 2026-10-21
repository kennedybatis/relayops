"""Check execution evidence against the three synthetic live scenarios."""

import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("trace")
a = p.parse_args()
events = [json.loads(line) for line in Path(a.trace).read_text().splitlines()]
assert events[0]["event"] == "started"
assert not any(e["event"] == "failed" for e in events), "Run contains a failure"
steps = [e for e in events if e["event"] == "tool_completed"]
assert steps and steps[-1]["action"]["tool"] == "finish", "No verified completion"
assert steps[-1]["result"]["verified_count"] == 3
assert steps[-1]["result"]["external_messages_sent"] == 0
assessments = {
    e["action"]["lead_id"]: e
    for e in steps
    if e["action"]["tool"] == "record_assessment"
}
expected = {
    "live-01": ("sales_ready", False),
    "live-02": ("needs_review", True),
    "live-03": ("needs_information", False),
}
for key, (status, conflict) in expected.items():
    event = assessments[key]
    assert event["result"]["status"] == status, (key, event["result"])
    if conflict:
        assert event["action"]["conflict"] or event["action"].get("budget_evidence"), (
            key,
            event["action"],
        )
source_path = Path(__file__).resolve().parent.parent / "data/live-leads.json"
sources = {row["id"]: row for row in json.loads(source_path.read_text())}
for key, event in assessments.items():
    assert event["action"].get("message_evidence") in sources[key]["message"], key
    assert event["action"]["message_evidence"], key
verified = {
    e["result"]["lead_id"]
    for e in steps
    if e["action"]["tool"] == "verify_record" and e["result"]["readback_verified"]
}
assert verified == set(expected)
assert sum(e["usage"].get("output_tokens", 0) for e in steps) > 0
print(
    json.dumps(
        {
            "scenario_checks": "passed",
            "leads_verified": 3,
            "tool_calls": len(steps),
            "input_tokens_sum": sum(e["usage"].get("input_tokens", 0) for e in steps),
            "output_tokens_sum": sum(e["usage"].get("output_tokens", 0) for e in steps),
            "external_messages_sent": 0,
        },
        indent=2,
    )
)
