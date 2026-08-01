from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_PATH = Path("data/daily_nav.csv")


def calculate_summary(group: pd.DataFrame) -> dict[str, object]:
    group = group.sort_values("TRADE_DATE").copy()
    group["DAILY_RETURN"] = group["NAV"].pct_change()
    group["RUNNING_PEAK"] = group["NAV"].cummax()
    group["DRAWDOWN"] = group["NAV"] / group["RUNNING_PEAK"] - 1

    total_return = group["NAV"].iloc[-1] / group["NAV"].iloc[0] - 1
    benchmark_return = (
        group["BENCHMARK_NAV"].iloc[-1]
        / group["BENCHMARK_NAV"].iloc[0]
        - 1
    )

    return {
        "FUND_ID": group["FUND_ID"].iloc[0],
        "TOTAL_RETURN": total_return,
        "BENCHMARK_RETURN": benchmark_return,
        "EXCESS_RETURN": total_return - benchmark_return,
        "ANNUALIZED_VOLATILITY": (
            group["DAILY_RETURN"].std(ddof=1) * np.sqrt(252)
        ),
        "MAX_DRAWDOWN": group["DRAWDOWN"].min(),
        "OBSERVATIONS": len(group),
    }


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "먼저 python 01_generate_sample_data.py를 실행하십시오."
        )

    dataframe = pd.read_csv(DATA_PATH)
    summaries = [
        calculate_summary(group)
        for _, group in dataframe.groupby("FUND_ID")
    ]
    result = pd.DataFrame(summaries)

    percentage_columns = [
        "TOTAL_RETURN",
        "BENCHMARK_RETURN",
        "EXCESS_RETURN",
        "ANNUALIZED_VOLATILITY",
        "MAX_DRAWDOWN",
    ]
    for column in percentage_columns:
        result[column] = result[column].map(
            lambda value: f"{value * 100:.2f}%"
        )

    print("[정상] 로컬 계산 결과")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
