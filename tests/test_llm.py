from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from openai import OpenAIError

from src.llm import explain_summary, rule_based_explanation


BALANCED_SUMMARY = {
    "FUND_ID": "KIRI_BALANCED",
    "PERIOD_START": "2026-01-02",
    "PERIOD_END": "2026-06-30",
    "TOTAL_RETURN": 0.040129226523,
    "BENCHMARK_RETURN": -0.019495577381,
    "EXCESS_RETURN": 0.059624803904,
    "ANNUALIZED_VOLATILITY": 0.085042,
    "MAX_DRAWDOWN": -0.059937371965,
    "OBSERVATIONS": 128,
}

GROWTH_SUMMARY = {
    "FUND_ID": "KIRI_GROWTH",
    "PERIOD_START": "2026-01-02",
    "PERIOD_END": "2026-06-30",
    "TOTAL_RETURN": -0.028812985477,
    "BENCHMARK_RETURN": -0.019495577381,
    "EXCESS_RETURN": -0.009317408096,
    "ANNUALIZED_VOLATILITY": 0.153381,
    "MAX_DRAWDOWN": -0.152916929688,
    "OBSERVATIONS": 128,
}


class LlmExplanationTests(unittest.TestCase):
    def test_balanced_rule_explanation(self) -> None:
        result = rule_based_explanation(BALANCED_SUMMARY)

        self.assertIn("4.01%", result)
        self.assertIn("5.96%", result)
        self.assertIn("벤치마크를 상회했습니다", result)
        self.assertIn("상대적으로 제한적입니다", result)

    def test_growth_rule_explanation(self) -> None:
        result = rule_based_explanation(GROWTH_SUMMARY)

        self.assertIn("-2.88%", result)
        self.assertIn("-0.93%", result)
        self.assertIn("벤치마크를 하회했습니다", result)
        self.assertIn("위험 수준이 비교적 높으므로", result)

    def test_missing_config_uses_rule_explanation(self) -> None:
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "", "OPENAI_MODEL": ""},
        ):
            with patch("src.llm.OpenAI") as mock_openai:
                result = explain_summary(BALANCED_SUMMARY)

        mock_openai.assert_not_called()
        self.assertIn("4.01%", result)
        self.assertIn("합성 데이터", result)

    def test_api_success_uses_safe_request_options(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_MODEL": "test-model",
            },
        ):
            with patch("src.llm.OpenAI") as mock_openai:
                mock_openai.return_value.responses.create.return_value = (
                    SimpleNamespace(output_text="테스트 LLM 설명")
                )

                result = explain_summary(BALANCED_SUMMARY)
                request = (
                    mock_openai.return_value.responses.create.call_args.kwargs
                )

        self.assertEqual(result, "테스트 LLM 설명")
        self.assertEqual(request["model"], "test-model")
        self.assertEqual(request["reasoning"], {"effort": "low"})
        self.assertEqual(request["text"], {"verbosity": "low"})
        self.assertEqual(request["max_output_tokens"], 500)
        self.assertFalse(request["store"])

    def test_api_failure_falls_back_to_rules(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_MODEL": "test-model",
            },
        ):
            with patch("src.llm.OpenAI") as mock_openai:
                mock_openai.return_value.responses.create.side_effect = (
                    OpenAIError("simulated failure")
                )

                result = explain_summary(BALANCED_SUMMARY)

        self.assertIn("규칙 기반 설명으로 전환했습니다", result)
        self.assertIn("4.01%", result)
        self.assertIn("5.96%", result)


if __name__ == "__main__":
    unittest.main()