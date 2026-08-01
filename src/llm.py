from __future__ import annotations

import os
from typing import Any

from openai import OpenAI, OpenAIError


def _percent(value: Any) -> str:
    return f"{float(value) * 100:.2f}%"


def rule_based_explanation(summary: dict[str, Any]) -> str:
    excess = float(summary["EXCESS_RETURN"])
    volatility = float(summary["ANNUALIZED_VOLATILITY"])
    max_drawdown = float(summary["MAX_DRAWDOWN"])

    relative = (
        "벤치마크를 상회했습니다."
        if excess > 0
        else "벤치마크를 하회했습니다."
    )

    risk_comment = (
        "위험 수준이 비교적 높으므로 손실 허용한도와 포지션 집중도를 "
        "추가 점검해야 합니다."
        if volatility >= 0.15 or max_drawdown <= -0.10
        else "관측기간의 변동성과 낙폭은 상대적으로 제한적입니다."
    )

    return f"""### 핵심 판단
- 관측기간 총수익률은 {_percent(summary['TOTAL_RETURN'])}이며, {relative}
- 벤치마크 대비 초과수익률은 {_percent(excess)}입니다.
- 연율화 변동성은 {_percent(volatility)}, 최대낙폭은 {_percent(max_drawdown)}입니다.

### 위험 해석
- {risk_comment}

### 주의사항
- 이 설명은 합성 데이터와 사전에 계산된 지표를 요약한 데모입니다.
- 투자 판단에는 포지션, 현금흐름, 거래비용, 위험한도 및 실제 시장상황을 추가 검토해야 합니다.
"""


def explain_summary(summary: dict[str, Any]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()

    if not api_key or not model or model == "YOUR_AVAILABLE_MODEL":
        return rule_based_explanation(summary)

    client = OpenAI(api_key=api_key)

    grounded_facts = f"""
펀드: {summary['FUND_ID']}
분석기간: {summary['PERIOD_START']} ~ {summary['PERIOD_END']}
총수익률: {_percent(summary['TOTAL_RETURN'])}
벤치마크수익률: {_percent(summary['BENCHMARK_RETURN'])}
초과수익률: {_percent(summary['EXCESS_RETURN'])}
연율화 변동성: {_percent(summary['ANNUALIZED_VOLATILITY'])}
최대낙폭: {_percent(summary['MAX_DRAWDOWN'])}
관측치 수: {int(summary['OBSERVATIONS'])}
"""

    try:
        response = client.responses.create(
            model=model,
            instructions=(
                "당신은 기관투자가용 성과·위험 분석 보조자다. "
                "제공된 수치를 다시 계산하거나 새로운 원인을 추측하지 말라. "
                "제공된 사실만 근거로 한국어로 작성하라. "
                "구성은 '핵심 판단, 성과 해석, 위험 해석, 추가 확인사항' "
                "순서로 한다. "
                "이 데이터가 합성 데모라는 사실을 명시하라."
            ),
            input=grounded_facts,
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
            max_output_tokens=500,
            store=False,
        )
        return response.output_text

    except OpenAIError as exc:
        print(f"[경고] OpenAI API 호출 실패: {type(exc).__name__}")
        return (
            "> ⚠️ OpenAI API 호출에 실패하여 규칙 기반 설명으로 전환했습니다.\n\n"
            + rule_based_explanation(summary)
        )