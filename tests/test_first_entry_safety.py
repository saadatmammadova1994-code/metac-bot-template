"""Offline tests for the single-question FutureEval workflow (no network or secrets)."""
from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/futureeval_first_entry.py").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/first_futureeval_entry.yml").read_text(encoding="utf-8")


class FakeBinaryQuestion:
    def __init__(self, id: int, *, close_time, previous_forecasts=None,
                 conditional_type=None):
        self.id_of_post = id
        self.close_time = close_time
        self.previous_forecasts = previous_forecasts
        self.conditional_type = conditional_type
        self.page_url = f"https://www.metaculus.com/questions/{id}"


class FakeOtherQuestion(FakeBinaryQuestion):
    pass


class FakeClient:
    def __init__(self, questions):
        self.questions = questions

    def get_all_open_questions_from_tournament(self, name, group_question_mode):
        assert name == "fall-futureeval-2026"
        assert group_question_mode == "exclude"
        return self.questions


def load_pure_selection_functions():
    tree = ast.parse(SCRIPT)
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in ("available_binary_questions", "select_question")
    ]
    module = ast.Module(
        body=[ast.ImportFrom(
            module="__future__", names=[ast.alias(name="annotations")], level=0),
            *nodes],
        type_ignores=[],
    )
    ns = {
        "BinaryQuestion": FakeBinaryQuestion,
        "TOURNAMENT": "fall-futureeval-2026",
        "MIN_TIME_TO_CLOSE": timedelta(hours=36),
        "timezone": timezone,
    }
    exec(compile(ast.fix_missing_locations(module), "<entry-selection>", "exec"), ns)
    return ns["available_binary_questions"], ns["select_question"]


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 8, tzinfo=timezone.utc)
        self.get_eligible, self.select = load_pure_selection_functions()

    def test_script_syntax(self):
        ast.parse(SCRIPT)

    def test_manual_only(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertNotIn("schedule:", WORKFLOW)
        self.assertIn("options:", WORKFLOW)
        self.assertIn("preview", WORKFLOW)

    def test_live_submit_requires_confirmed_question_id(self):
        self.assertIn('acknowledgement != "true" or not question_id', SCRIPT)
        self.assertIn('if mode == "submit":', SCRIPT)

    def test_free_tier_gate(self):
        self.assertIn('if free_tier != "true":', SCRIPT)
        self.assertIn('confirm_free_tier:', WORKFLOW)
        self.assertIn('test "$FIRST_ENTRY_FREE_TIER_CONFIRMED" = "true"', WORKFLOW)

    def test_no_paid_ai_or_research_in_script(self):
        self.assertIn('llms=free_model_config()', SCRIPT)
        self.assertNotIn("OPENROUTER_API_KEY", SCRIPT)
        self.assertNotIn("ASKNEWS", SCRIPT.upper())

    def test_publish_is_only_explicit_submit(self):
        self.assertIn('publish_reports_to_metaculus=(mode == "submit")', SCRIPT)
        self.assertIn('skip_previously_forecasted_questions=True', SCRIPT)
        self.assertIn("forecast_questions([selected]", SCRIPT)

    def test_filters_already_forecast(self):
        q = FakeBinaryQuestion(111, close_time=self.now+timedelta(days=8), previous_forecasts=[0.4])
        self.assertEqual(self.get_eligible(FakeClient([q]),self.now), [])

    def test_filters_closed_soon(self):
        q = FakeBinaryQuestion(111, close_time=self.now+timedelta(hours=8))
        self.assertEqual(self.get_eligible(FakeClient([q]),self.now), [])

    def test_filters_conditional_question(self):
        q = FakeBinaryQuestion(111, close_time=self.now+timedelta(days=8),
                               conditional_type="yes")
        self.assertEqual(self.get_eligible(FakeClient([q]),self.now), [])

    def test_filters_naive_close_time(self):
        q = FakeBinaryQuestion(111, close_time=datetime(2026, 12, 1))
        self.assertEqual(self.get_eligible(FakeClient([q]),self.now), [])

    def test_picks_near_7_days(self):
        a = FakeBinaryQuestion(101, close_time=self.now+timedelta(days=15))
        b = FakeBinaryQuestion(102, close_time=self.now+timedelta(days=7))
        c = FakeBinaryQuestion(103, close_time=self.now+timedelta(days=3))
        x=self.get_eligible(FakeClient([a,b,c]),self.now)
        self.assertEqual(self.select(x,"").id_of_post,102)

    def test_does_not_choose_wrong_question_id(self):
        q = FakeBinaryQuestion(101, close_time=self.now+timedelta(days=7))
        with self.assertRaises(ValueError):
            self.select([q],"102")

    def test_requires_numeric_question_id(self):
        q = FakeBinaryQuestion(101, close_time=self.now+timedelta(days=7))
        with self.assertRaises(ValueError):
            self.select([q],"101;rm -rf /")

    def test_empty_question_list_refuses(self):
        with self.assertRaises(ValueError):
            self.select([],"")

    def test_user_submitted_id_is_honored(self):
        qs=[FakeBinaryQuestion(100,close_time=self.now+timedelta(days=7)),
            FakeBinaryQuestion(200,close_time=self.now+timedelta(days=8))]
        self.assertEqual(self.select(qs,"200").id_of_post,200)

    def test_requires_locked_dependencies(self):
        self.assertIn("uv sync --locked", WORKFLOW)

if __name__ == "__main__":
    unittest.main()
