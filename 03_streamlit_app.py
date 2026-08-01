from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db import query_dataframe
from src.llm import explain_summary


st.set_page_config(
    page_title="KIRI Fund Decision Demo",
    page_icon="📊",
    layout="wide",
)

st.title("KIRI 펀드 성과·위험 분석 데모")
st.caption(
    "합성 데이터 → Snowflake → SQL 계산 → Python 조회 "
    "→ Streamlit 표시 → LLM 설명"
)


@st.cache_data(ttl=300)
def load_fund_list() -> list[str]:
    dataframe = query_dataframe(
        """
        SELECT DISTINCT FUND_ID
        FROM KIRI_AI_DEMO.MART.V_FUND_SUMMARY
        ORDER BY FUND_ID
        """
    )
    return dataframe["FUND_ID"].tolist()


@st.cache_data(ttl=300)
def load_summary(fund_id: str) -> pd.DataFrame:
    return query_dataframe(
        """
        SELECT *
        FROM KIRI_AI_DEMO.MART.V_FUND_SUMMARY
        WHERE FUND_ID = %s
        """,
        (fund_id,),
    )


@st.cache_data(ttl=300)
def load_daily_data(fund_id: str) -> pd.DataFrame:
    return query_dataframe(
        """
        SELECT
            TRADE_DATE,
            NAV,
            BENCHMARK_NAV,
            DAILY_RETURN,
            DRAWDOWN
        FROM KIRI_AI_DEMO.MART.V_DAILY_PERFORMANCE
        WHERE FUND_ID = %s
        ORDER BY TRADE_DATE
        """,
        (fund_id,),
    )


try:
    funds = load_fund_list()
except Exception as error:
    st.error(
        "Snowflake 연결 또는 조회에 실패했습니다. "
        ".env와 02_load_and_transform.py 실행 결과를 확인하십시오."
    )
    st.exception(error)
    st.stop()

selected_fund = st.sidebar.selectbox(
    "분석할 펀드",
    options=funds,
)

summary_df = load_summary(selected_fund)
daily_df = load_daily_data(selected_fund)

if summary_df.empty:
    st.warning("선택한 펀드의 요약 데이터가 없습니다.")
    st.stop()

summary = summary_df.iloc[0].to_dict()

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "총수익률",
    f"{summary['TOTAL_RETURN'] * 100:.2f}%",
)
col2.metric(
    "초과수익률",
    f"{summary['EXCESS_RETURN'] * 100:.2f}%",
)
col3.metric(
    "연율화 변동성",
    f"{summary['ANNUALIZED_VOLATILITY'] * 100:.2f}%",
)
col4.metric(
    "최대낙폭",
    f"{summary['MAX_DRAWDOWN'] * 100:.2f}%",
)

st.subheader("기준가 추이")
chart_df = daily_df.set_index("TRADE_DATE")[
    ["NAV", "BENCHMARK_NAV"]
]
st.line_chart(chart_df)

left, right = st.columns(2)

with left:
    st.subheader("SQL 계산 결과")
    display_summary = summary_df.copy()
    percentage_columns = [
        "TOTAL_RETURN",
        "BENCHMARK_RETURN",
        "EXCESS_RETURN",
        "ANNUALIZED_VOLATILITY",
        "MAX_DRAWDOWN",
    ]
    for column in percentage_columns:
        display_summary[column] = display_summary[column].map(
            lambda value: f"{value * 100:.2f}%"
        )
    st.dataframe(
        display_summary,
        width="stretch",
        hide_index=True,
    )

with right:
    st.subheader("LLM 설명")
    st.caption(
        "API 키·모델이 없으면 규칙 기반 설명이 표시됩니다."
    )
    if st.button("분석 설명 생성", type="primary"):
        with st.spinner("설명 생성 중..."):
            try:
                explanation = explain_summary(summary)
                st.markdown(explanation)
            except Exception as error:
                st.error("LLM 설명 생성에 실패했습니다.")
                st.exception(error)

with st.expander("일별 계산 데이터 확인"):
    st.dataframe(
        daily_df,
        width="stretch",
        hide_index=True,
    )

st.info(
    "이 앱의 수익률·변동성·최대낙폭은 Snowflake SQL이 계산하고, "
    "LLM은 계산된 결과를 설명만 합니다."
)
