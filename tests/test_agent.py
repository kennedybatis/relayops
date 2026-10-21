import copy
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit
from relayops.agent import (
    WorkspaceTools,
    OllamaPlanner,
    INPUT_HEADERS,
    OUTPUT_HEADERS,
    run_agent,
    BridgeTransport,
)
from relayops.connectors import GoogleSheets


class SheetDouble:
    def __init__(self):
        self.leads = [
            INPUT_HEADERS,
            [
                "test-01",
                "Pessoa fictícia",
                "person@example.invalid",
                650000,
                60,
                True,
                "O orçamento correto é 200 mil, não 650 mil.",
            ],
        ]
        self.rows = {"AgentReview!A1:G1": [OUTPUT_HEADERS]}
        self.requests = []

    def __call__(self, request):
        area = unquote(urlsplit(request.full_url).path.split("/values/")[1])
        self.requests.append((request.get_method(), area))
        if request.get_method() == "PUT":
            self.rows[area] = json.loads(request.data)["values"]
            return {"updatedRows": 1}
        return {
            "values": copy.deepcopy(
                self.leads if area == "Leads!A1:G11" else self.rows.get(area, [])
            )
        }


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.sheet = SheetDouble()
        self.tools = WorkspaceTools(GoogleSheets("test", "not-a-secret", self.sheet))
        self.args = {
            "lead_id": "test-01",
            "summary": "Mensagem contradiz orçamento do formulário.",
            "next_action": "Confirmar orçamento com o lead.",
            "conflict": True,
            "message_evidence": "O orçamento correto é 200 mil, não 650 mil.",
        }

    def prepare(self):
        self.tools.execute("read_campaign", {})
        self.tools.execute("read_leads", {})

    def test_cannot_write_before_reading(self):
        with self.assertRaises(ValueError):
            self.tools.execute("record_assessment", self.args)

    def test_model_cannot_approve_send_or_delete(self):
        self.prepare()
        for tool in ("approve", "send", "delete", "shell"):
            with self.assertRaises(ValueError):
                self.tools.execute(tool, {})

    def test_conflict_flag_and_verified_write(self):
        self.prepare()
        result = self.tools.execute("record_assessment", self.args)
        self.assertEqual(result["status"], "needs_review")
        self.assertNotIn("finish", self.tools.available())
        self.assertTrue(
            self.tools.execute("verify_record", {"lead_id": "test-01"})[
                "readback_verified"
            ]
        )
        self.assertTrue(self.tools.execute("finish", {})["completed"])

    def test_quoted_budget_overrides_missed_model_conflict(self):
        self.prepare()
        args = dict(self.args, conflict=False, budget_evidence="200 mil")
        self.assertEqual(
            self.tools.execute("record_assessment", args)["status"], "needs_review"
        )

    def test_source_budget_ambiguity_survives_wrong_model_quote(self):
        self.prepare()
        wrong = dict(self.args, conflict=False, budget_evidence="650 mil")
        result = self.tools.execute("record_assessment", wrong)
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("validação humana", self.tools.writes["test-01"]["values"][3])

    def test_canonical_summary_uses_source_not_model_invention(self):
        self.prepare()
        invented = dict(
            self.args, summary="A pessoa tem um negócio concluído e vendeu um imóvel."
        )
        self.tools.execute("record_assessment", invented)
        saved = self.tools.writes["test-01"]["values"][2]
        self.assertIn(self.args["message_evidence"], saved)
        self.assertNotIn("concluído", saved)

    def test_fabricated_message_evidence_is_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError):
            self.tools.execute(
                "record_assessment",
                dict(self.args, message_evidence="Quero comprar amanhã."),
            )
        self.assertFalse(any(method == "PUT" for method, _ in self.sheet.requests))

    def test_fabricated_budget_evidence_is_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError):
            self.tools.execute(
                "record_assessment", dict(self.args, budget_evidence="900 mil")
            )
        self.assertFalse(any(method == "PUT" for method, _ in self.sheet.requests))

    def test_budget_amount_parser_is_conservative(self):
        from relayops.agent import parse_budget_evidence

        self.assertEqual(parse_budget_evidence("200 mil reais"), 200000)
        self.assertEqual(parse_budget_evidence("R$ 650.000"), 650000)
        self.assertIsNone(parse_budget_evidence("cerca de muito dinheiro"))

    def test_no_consent_overrides_model_flag(self):
        self.sheet.leads[1][5] = False
        self.prepare()
        self.assertEqual(
            self.tools.execute("record_assessment", self.args)["status"], "no_contact"
        )

    def test_template_assessment_is_rejected_before_write(self):
        self.prepare()
        invalid = dict(self.args, summary="Lead: [Lead ID] - [Lead Summary]")
        with self.assertRaises(ValueError):
            self.tools.execute("record_assessment", invalid)
        self.assertFalse(any(method == "PUT" for method, _ in self.sheet.requests))

    def test_changed_source_stops_write(self):
        self.prepare()
        self.sheet.leads[1][3] = 100
        with self.assertRaises(ValueError):
            self.tools.execute("record_assessment", self.args)
        self.assertFalse(any(method == "PUT" for method, _ in self.sheet.requests))

    def test_occupied_output_is_preserved(self):
        self.prepare()
        self.sheet.rows["AgentReview!A2:G2"] = [["existing review"]]
        with self.assertRaises(ValueError):
            self.tools.execute("record_assessment", self.args)

    def test_readback_mismatch_prevents_completion(self):
        self.prepare()
        self.tools.execute("record_assessment", self.args)
        self.sheet.rows["AgentReview!A2:G2"] = [["tampered"]]
        with self.assertRaises(RuntimeError):
            self.tools.execute("verify_record", {"lead_id": "test-01"})
        self.assertNotIn("finish", self.tools.available())

    def test_finish_rechecks_previous_verification(self):
        self.prepare()
        self.tools.execute("record_assessment", self.args)
        self.tools.execute("verify_record", {"lead_id": "test-01"})
        self.sheet.rows["AgentReview!A2:G2"] = [["tampered"]]
        with self.assertRaises(RuntimeError):
            self.tools.execute("finish", {})

    def test_network_failure_is_not_retried(self):
        self.prepare()
        transport = self.tools.connector.transport

        def fail(request):
            if request.get_method() == "PUT":
                raise TimeoutError("network")
            return transport(request)

        self.tools.connector.transport = fail
        with self.assertRaises(TimeoutError):
            self.tools.execute("record_assessment", self.args)
        self.assertIn("test-01", self.tools.writes)
        with self.assertRaises(ValueError):
            self.tools.execute("record_assessment", self.args)

    def test_planner_structured_allowed_actions(self):
        def transport(req):
            body = json.loads(req.data)
            self.assertEqual(
                body["format"]["oneOf"][0]["properties"]["tool"]["const"], "read_leads"
            )
            return {"message": {"content": json.dumps({"tool": "read_leads"})}}

        planner = OllamaPlanner("fake-contract", transport)
        action, _ = planner.choose(
            [],
            {
                "allowed_tools": ["read_leads"],
                "unassessed_ids": [],
                "unverified_ids": [],
            },
        )
        self.assertEqual(action["tool"], "read_leads")

    def test_loop_limits_incomplete_execution(self):
        class Planner:
            model = "scripted-test"

            def choose(self, messages, state):
                return {
                    "tool": state["allowed_tools"][0],
                    "lead_id": "",
                    "summary": "",
                    "next_action": "",
                    "conflict": False,
                }, {}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            with self.assertRaises(RuntimeError):
                run_agent("test", Planner(), self.tools, path, max_steps=1)
            self.assertIn("StepLimit", path.read_text())

    def test_bridge_timeout_does_not_infer_success(self):
        from urllib.request import Request

        with tempfile.TemporaryDirectory() as directory:
            bridge = BridgeTransport(directory, timeout=0)
            with self.assertRaises(TimeoutError):
                bridge(Request("https://sheets.googleapis.com/test"))


if __name__ == "__main__":
    unittest.main()
