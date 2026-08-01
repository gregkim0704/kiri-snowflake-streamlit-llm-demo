from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path("data/daily_nav.csv")


def main() -> None:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2026-01-02", "2026-06-30")
    observations = len(dates)

    benchmark_returns = rng.normal(
        loc=0.00025,
        scale=0.009,
        size=observations,
    )
    growth_returns = (
        0.00015
        + 1.15 * benchmark_returns
        + rng.normal(0, 0.0045, observations)
    )
    balanced_returns = (
        0.00018
        + 0.65 * benchmark_returns
        + rng.normal(0, 0.0025, observations)
    )

    benchmark_nav = 1000 * np.cumprod(1 + benchmark_returns)
    rows: list[dict[str, object]] = []

    for fund_id, returns in {
        "KIRI_GROWTH": growth_returns,
        "KIRI_BALANCED": balanced_returns,
    }.items():
        nav = 1000 * np.cumprod(1 + returns)

        for trade_date, fund_nav, bm_nav in zip(
            dates,
            nav,
            benchmark_nav,
        ):
            rows.append(
                {
                    "TRADE_DATE": trade_date.date(),
                    "FUND_ID": fund_id,
                    "NAV": round(float(fund_nav), 6),
                    "BENCHMARK_NAV": round(float(bm_nav), 6),
                }
            )

    dataframe = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[정상] 생성 파일: {OUTPUT_PATH.resolve()}")
    print(f"[정상] 행 수: {len(dataframe):,}")
    print(dataframe.head())


if __name__ == "__main__":
    main()
