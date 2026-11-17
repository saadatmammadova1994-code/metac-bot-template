"""Static safety regression tests for the manual-only free Metaculus smoke test."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestFreeSmokeSafety(unittest.TestCase):
    def test_script_compiles(self):
        source = (ROOT / "scripts/free_single_question_test.py").read_text()
        ast.parse(source)

    def test_explicit_free_model(self):
        source = (ROOT / "scripts/free_single_question_test.py").read_text()
        self.assertIn('FREE_MODEL = "gemini/gemini-3.1-flash-lite"', source)
        self.assertIn('FREE_MODEL != "gemini/gemini-3.1-flash-lite"', source)
        self.assertIn('"researcher": "no_research"', source)
        self.assertIn("llms=free_model_config()", source)
        self.assertIn('os.getenv("GEMINI_API_KEY")', source)
        self.assertNotIn("OPENROUTER_API_KEY", source)
        self.assertIn("forecast_questions([binary]", source)

    def test_test_workflow_manual_only(self):
        workflow = (ROOT / ".github/workflows/test_bot.yaml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("scripts/free_single_question_test.py", workflow)


if __name__ == "__main__":
    unittest.main()
