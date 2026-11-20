import time
import unittest
from unittest.mock import patch
from agent.search import search


class TestSearch(unittest.TestCase):
    @patch("agent.search.time.sleep")
    @patch("agent.search._fetch")
    def test_empty_results_returns_empty_list(self, mock_fetch, _mock_sleep):
        mock_fetch.return_value = []
        results = search("empty query", retries=1)
        self.assertEqual(results, [])

    @patch("agent.search.time.sleep")
    @patch("agent.search._fetch")
    def test_exception_degrades_to_empty_list(self, mock_fetch, _mock_sleep):
        mock_fetch.side_effect = RuntimeError("network error")
        results = search("broken query", retries=1)
        self.assertEqual(results, [])

    @patch("agent.search.time.sleep")
    @patch("agent.search._fetch")
    def test_timeout_degrades_to_empty_list(self, mock_fetch, _mock_sleep):
        def slow_fetch(*args, **kwargs):
            time.sleep(0.3)
            return []

        mock_fetch.side_effect = slow_fetch
        results = search("slow query", retries=0, timeout=0.05)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()