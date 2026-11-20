import unittest
from unittest.mock import patch
from agent import loop
from agent.models import SearchResult


class TestLoop(unittest.TestCase):
    @patch("agent.loop._save_run")
    @patch("agent.loop.time.sleep")
    @patch("agent.loop._generate_report")
    @patch("agent.loop._judge")
    @patch("agent.loop.search")
    @patch("agent.loop._plan_queries")
    def test_stops_at_max_rounds(
        self,
        mock_plan,
        mock_search,
        mock_judge,
        mock_generate,
        _mock_sleep,
        _mock_save,
    ):
        counter = {"n": 0}

        def fake_search(q, max_results=5):
            counter["n"] += 1
            return [
                SearchResult(
                    title=f"Title {counter['n']}",
                    url=f"https://example.com/{counter['n']}",
                    snippet="snippet",
                    query=q,
                    round=0,
                )
            ]

        mock_plan.return_value = ["query 1"]
        mock_search.side_effect = fake_search
        mock_judge.return_value = {
            "enough": False,
            "reason": "still need more",
            "new_queries": ["next query"],
        }
        mock_generate.return_value = {
            "background": "bg",
            "findings": [{"claim": "c1", "source": "https://example.com/1"}],
            "disagreements": [],
        }

        report = loop.run("test topic")

        search_steps = [s for s in report.steps if s.action == "search"]
        self.assertEqual(len(search_steps), loop.MAX_ROUNDS)
        self.assertEqual(report.status, "ok")

    @patch("agent.loop._save_run")
    @patch("agent.loop._plan_queries")
    def test_internal_exception_returns_failed_report(self, mock_plan, _mock_save):
        mock_plan.side_effect = RuntimeError("unexpected crash")
        report = loop.run("test topic")
        self.assertEqual(report.status, "failed")


if __name__ == "__main__":
    unittest.main()