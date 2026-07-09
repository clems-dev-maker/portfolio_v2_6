from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PerformanceBundle:
    summary: pd.DataFrame
    monthly_returns: pd.DataFrame
    annual_returns: pd.DataFrame
    attribution: pd.DataFrame
    benchmark: pd.DataFrame


def _amount(df: pd.DataFrame) -> pd.Series:
    if "amount" not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)


def _type(df: pd.DataFrame) -> pd.Series:
    if "type" not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype=str)
    return df["type"].astype(str).str.upper().fillna("")


def _date(df: pd.DataFrame) -> pd.Series:
    if "date" not in df.columns:
        return pd.Series(pd.NaT, index=df.index)
    return pd.to_datetime(df["date"], errors="coerce")


def _xnpv(rate: float, cashflows: list[tuple[pd.Timestamp, float]]) -> float:
    if not cashflows:
        return 0.0
    d0 = cashflows[0][0]
    total = 0.0
    for d, cf in cashflows:
        days = (d - d0).days
        total += cf / ((1.0 + rate) ** (days / 365.25))
    return total


def xirr(cashflows: list[tuple[pd.Timestamp, float]]) -> float | None:
    """Robust XIRR approximation using bisection.

    Convention: investor cash outflows are negative, ending portfolio value is positive.
    """
    cashflows = [(pd.Timestamp(d), float(v)) for d, v in cashflows if pd.notna(d) and math.isfinite(float(v))]
    if not cashflows or not any(v < 0 for _, v in cashflows) or not any(v > 0 for _, v in cashflows):
        return None

    lo, hi = -0.9999, 10.0
    f_lo, f_hi = _xnpv(lo, cashflows), _xnpv(hi, cashflows)
    # Expand upper bound if needed.
    for _ in range(20):
        if f_lo * f_hi <= 0:
            break
        hi *= 2
        f_hi = _xnpv(hi, cashflows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        f_mid = _xnpv(mid, cashflows)
        if abs(f_mid) < 1e-7:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def _cashflows_for_xirr(transactions: pd.DataFrame, portfolio_value: float, last_date: pd.Timestamp | None) -> list[tuple[pd.Timestamp, float]]:
    df = transactions.copy()
    df["date_norm"] = _date(df)
    df = df.dropna(subset=["date_norm"])
    if df.empty:
        return []
    typ = _type(df)
    amount = _amount(df)

    # Convention investisseur : achats/apports = sorties négatives ; ventes/dividendes/intérêts = entrées positives.
    signed = pd.Series(0.0, index=df.index)
    signed = signed.where(~typ.eq("BUY"), -amount.abs())
    signed = signed.where(~typ.eq("SELL"), amount.abs())
    income_mask = typ.str.contains("DIVIDEND|INTEREST|CASH|INCOME", regex=True, na=False)
    signed = signed.where(~income_mask, amount.abs())

    flows = [(pd.Timestamp(d), float(v)) for d, v in zip(df["date_norm"], signed) if abs(float(v)) > 1e-9]
    end_date = pd.Timestamp(last_date) if last_date is not None and pd.notna(last_date) else pd.Timestamp(df["date_norm"].max())
    flows.append((end_date, float(portfolio_value)))
    return sorted(flows, key=lambda x: x[0])


def build_monthly_performance(transactions: pd.DataFrame, portfolio_value: float) -> pd.DataFrame:
    df = transactions.copy()
    df["date_norm"] = _date(df)
    df = df.dropna(subset=["date_norm"])
    if df.empty:
        return pd.DataFrame(columns=["month", "net_contribution", "capital_invested", "estimated_value", "estimated_return", "cumulative_return"])

    typ = _type(df)
    amt = _amount(df)
    buy = amt.where(typ.eq("BUY"), 0.0).abs()
    sell = amt.where(typ.eq("SELL"), 0.0).abs()
    income = amt.where(typ.str.contains("DIVIDEND|INTEREST|INCOME", regex=True, na=False), 0.0).abs()
    df["net_contribution"] = buy - sell - income
    df["month"] = df["date_norm"].dt.to_period("M").astype(str)
    monthly = df.groupby("month", as_index=False)["net_contribution"].sum()
    monthly["capital_invested"] = monthly["net_contribution"].cumsum().clip(lower=0.0)
    final_capital = float(monthly["capital_invested"].iloc[-1]) if len(monthly) else 0.0
    final_pnl = float(portfolio_value - final_capital)
    if final_capital > 0:
        progress = monthly["capital_invested"] / final_capital
        monthly["estimated_value"] = monthly["capital_invested"] + final_pnl * progress
    else:
        monthly["estimated_value"] = portfolio_value
    previous_value = monthly["estimated_value"].shift(1).fillna(monthly["capital_invested"].replace(0, np.nan)).replace(0, np.nan)
    monthly["estimated_return"] = (monthly["estimated_value"] - monthly["estimated_value"].shift(1).fillna(0) - monthly["net_contribution"]) / previous_value
    monthly["estimated_return"] = monthly["estimated_return"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    monthly["cumulative_return"] = (1.0 + monthly["estimated_return"]).cumprod() - 1.0
    return monthly


def build_annual_returns(monthly: pd.DataFrame) -> pd.DataFrame:
    if monthly.empty or "month" not in monthly.columns:
        return pd.DataFrame(columns=["year", "annual_return", "contribution", "ending_value"])
    df = monthly.copy()
    df["year"] = df["month"].astype(str).str.slice(0, 4)
    out = df.groupby("year", as_index=False).agg(
        annual_return=("estimated_return", lambda s: float((1.0 + s).prod() - 1.0)),
        contribution=("net_contribution", "sum"),
        ending_value=("estimated_value", "last"),
    )
    return out


def build_attribution(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame(columns=["name", "asset_class", "net_contribution", "weight"])
    df = transactions.copy()
    name = df["name"].fillna("Non renseigné").astype(str) if "name" in df.columns else pd.Series("Non renseigné", index=df.index)
    cls = df["asset_class"].fillna("Non classé").astype(str) if "asset_class" in df.columns else pd.Series("Non classé", index=df.index)
    typ = _type(df)
    amt = _amount(df)
    df["name"] = name
    df["asset_class"] = cls
    df["net_contribution"] = amt.where(typ.eq("BUY"), 0.0).abs() - amt.where(typ.eq("SELL"), 0.0).abs()
    grouped = df.groupby(["name", "asset_class"], as_index=False)["net_contribution"].sum()
    grouped = grouped[grouped["net_contribution"].abs() > 1e-9]
    total = grouped["net_contribution"].abs().sum()
    grouped["weight"] = grouped["net_contribution"].abs() / total if total else 0.0
    return grouped.sort_values("net_contribution", ascending=False).reset_index(drop=True)


def build_benchmark(monthly: pd.DataFrame, annual_assumption: float = 0.07) -> pd.DataFrame:
    if monthly.empty:
        return pd.DataFrame(columns=["month", "portfolio_index", "benchmark_index", "relative_performance"])
    df = monthly[["month", "estimated_return"]].copy()
    monthly_bench = (1.0 + annual_assumption) ** (1.0 / 12.0) - 1.0
    df["portfolio_index"] = 100.0 * (1.0 + df["estimated_return"]).cumprod()
    df["benchmark_index"] = 100.0 * ((1.0 + monthly_bench) ** (np.arange(len(df)) + 1))
    df["relative_performance"] = df["portfolio_index"] / df["benchmark_index"] - 1.0
    return df


def build_performance(transactions: pd.DataFrame, net_worth, metrics) -> PerformanceBundle:
    portfolio_value = float(net_worth.total_value or 0.0)
    monthly = build_monthly_performance(transactions, portfolio_value)
    annual = build_annual_returns(monthly)
    attribution = build_attribution(transactions)
    benchmark = build_benchmark(monthly)

    dates = _date(transactions).dropna()
    first_date = pd.Timestamp(dates.min()) if len(dates) else None
    last_date = pd.Timestamp(dates.max()) if len(dates) else None
    years = max(((last_date - first_date).days / 365.25), 1 / 365.25) if first_date is not None and last_date is not None else 0.0
    total_return = (metrics.pnl_estimate / metrics.invested_estimate) if getattr(metrics, "invested_estimate", 0) else 0.0
    cagr = (portfolio_value / metrics.invested_estimate) ** (1 / years) - 1 if metrics.invested_estimate > 0 and years > 0 else 0.0
    xirr_value = xirr(_cashflows_for_xirr(transactions, portfolio_value, last_date))
    best_month = float(monthly["estimated_return"].max()) if not monthly.empty else 0.0
    worst_month = float(monthly["estimated_return"].min()) if not monthly.empty else 0.0
    positive_months = float((monthly["estimated_return"] > 0).mean()) if not monthly.empty else 0.0
    benchmark_rel = float(benchmark["relative_performance"].iloc[-1]) if not benchmark.empty else 0.0

    summary = pd.DataFrame(
        [
            ("Performance totale estimée", total_return),
            ("CAGR estimé", cagr),
            ("XIRR estimé", xirr_value if xirr_value is not None else np.nan),
            ("Meilleur mois estimé", best_month),
            ("Pire mois estimé", worst_month),
            ("Mois positifs", positive_months),
            ("Sur/sous-performance vs benchmark 7%", benchmark_rel),
            ("Capital investi estimé", float(metrics.invested_estimate)),
            ("Valeur finale", portfolio_value),
        ],
        columns=["Indicateur", "Valeur"],
    )
    return PerformanceBundle(summary, monthly, annual, attribution, benchmark)


def perf_value(summary: pd.DataFrame, label: str) -> float:
    if summary.empty:
        return 0.0
    row = summary[summary["Indicateur"].eq(label)]
    if row.empty:
        return 0.0
    value = row.iloc[0]["Valeur"]
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0
