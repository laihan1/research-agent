import unittest
from unittest.mock import MagicMock, patch
from agent import llm


class TestLLM(unittest.TestCase):
    def test_fallback_from_groq_to_gemini(self):
        mock_groq = MagicMock(side_effect=RuntimeError("groq down"))
        mock_gemini = MagicMock(return_value="ok from gemini")
        mock_openrouter = MagicMock(return_value="ok from openrouter")

        with patch.dict(
            llm._CALLERS,
            {"groq": mock_groq, "gemini": mock_gemini, "openrouter": mock_openrouter},
        ):
            result = llm.complete("hello")

        self.assertEqual(result, "ok from gemini")
        mock_groq.assert_called_once()
        mock_gemini.assert_called_once()
        mock_openrouter.assert_not_called()

    def test_fallback_to_openrouter_when_first_two_fail(self):
        mock_groq = MagicMock(side_effect=RuntimeError("groq down"))
        mock_gemini = MagicMock(side_effect=RuntimeError("gemini down"))
        mock_openrouter = MagicMock(return_value="ok from openrouter")

        with patch.dict(
            llm._CALLERS,
            {"groq": mock_groq, "gemini": mock_gemini, "openrouter": mock_openrouter},
        ):
            result = llm.complete("hello")

        self.assertEqual(result, "ok from openrouter")

    def test_all_providers_fail_raises_llm_unavailable(self):
        fail = MagicMock(side_effect=RuntimeError("down"))

        with patch.dict(
            llm._CALLERS,
            {"groq": fail, "gemini": fail, "openrouter": fail},
        ):
            with self.assertRaises(llm.LLMUnavailable):
                llm.complete("hello")


if __name__ == "__main__":
    unittest.main()