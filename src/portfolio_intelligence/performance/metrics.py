from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class DashboardMetrics:
    portfolio_value: float
    invested_estimate: float
    pnl_estimate: float
    pnl_percent: float
    transaction_count: int
    position_count_estimate: int
    first_date: str | None
    last_date: str | None
    fees: float
    dividends: float
    interests: float


def estimate_position_count(transactions: pd.DataFrame) -> int:
    if "name" not in transactions.columns or "type" not in transactions.columns:
        return 0
    buys = transactions[transactions["type"].astype(str).str.upper().eq("BUY")]
    return int(buys["name"].dropna().nunique())


def build_dashboard_metrics(transactions: pd.DataFrame, tx_summary, net_worth) -> DashboardMetrics:
    portfolio_value = float(net_worth.total_value or 0.0)
    invested_estimate = max(float(tx_summary.buys - tx_summary.sells - tx_summary.dividends - tx_summary.interests + tx_summary.fees), 0.0)
    pnl_estimate = portfolio_value - invested_estimate if portfolio_value else 0.0
    pnl_percent = (pnl_estimate / invested_estimate * 100.0) if invested_estimate > 0 else 0.0
    if not math.isfinite(pnl_percent):
        pnl_percent = 0.0
    return DashboardMetrics(
        portfolio_value=portfolio_value,
        invested_estimate=invested_estimate,
        pnl_estimate=pnl_estimate,
        pnl_percent=pnl_percent,
        transaction_count=tx_summary.rows,
        position_count_estimate=estimate_position_count(transactions),
        first_date=tx_summary.first_date,
        last_date=tx_summary.last_date,
        fees=tx_summary.fees,
        dividends=tx_summary.dividends,
        interests=tx_summary.interests,
    )


def monthly_flows(transactions: pd.DataFrame) -> pd.DataFrame:
    if "date" not in transactions.columns:
        return pd.DataFrame(columns=["month", "amount"])
    df = transactions.copy()
    df = df.dropna(subset=["date"])
    amount = df["amount"] if "amount" in df.columns else 0.0
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df.assign(amount=amount).groupby("month", as_index=False)["amount"].sum()
