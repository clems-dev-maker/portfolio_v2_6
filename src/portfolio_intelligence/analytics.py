from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class AnalyticsBundle:
    class_allocation: pd.DataFrame
    sector_allocation: pd.DataFrame
    geography_allocation: pd.DataFrame
    currency_allocation: pd.DataFrame
    positions_estimated: pd.DataFrame
    monthly_evolution: pd.DataFrame
    top_positions: pd.DataFrame


SECTOR_RULES: list[tuple[tuple[str, ...], str]] = [
    (("nvidia", "asml", "semiconductor", "semi", "micron", "applied materials", "besi", "optoelectronics", "digital"), "Technologie / Semi-conducteurs"),
    (("amazon", "hermes", "lotus", "bakery", "bakeries", "luxe"), "Consommation / Luxe"),
    (("amgen", "intuitive", "viking", "therapeutics", "health", "medical"), "Santé"),
    (("gold", "silver", "palladium", "mining", "physical"), "Métaux précieux"),
    (("energy", "uranium", "nuclear", "solar", "gaztransport", "gtt", "lng"), "Énergie"),
    (("abb", "exail", "lynas", "rare earth", "industrial"), "Industrie / Matières stratégiques"),
    (("bond", "ibonds", "dez.", "aug.", "sept."), "Obligations"),
    (("bitcoin", "ethereum", "solana", "cardano", "crypto"), "Crypto"),
    (("msci", "s&p", "sp 500", "world", "euro stoxx", "nasdaq", "core"), "ETF actions diversifiés"),
]

GEO_RULES: list[tuple[tuple[str, ...], str]] = [
    (("usa", "s&p", "sp 500", "nasdaq", "nvidia", "amazon", "amgen", "micron", "intuitive", "viking", "coinbase", "applied digital"), "États-Unis"),
    (("europe", "euro stoxx", "hermes", "lotus", "asml", "besi", "abb", "exail", "gaztransport"), "Europe"),
    (("japan", "jpy"), "Japon"),
    (("emerging", "india", "china", "msci india"), "Émergents"),
    (("lynas", "australia"), "Australie"),
    (("world", "quality", "core msci"), "Monde développé"),
]

CURRENCY_RULES: list[tuple[tuple[str, ...], str]] = [
    (("usd", "s&p", "sp 500", "nasdaq", "nvidia", "amazon", "amgen", "micron", "bitcoin", "ethereum", "solana", "cardano"), "USD"),
    (("eur", "euro", "hermes", "lotus", "asml", "besi", "exail", "gaztransport"), "EUR"),
    (("jpy", "japan"), "JPY"),
    (("chf", "abb"), "CHF"),
    (("aud", "lynas"), "AUD"),
]


def _normalize_name(value: object) -> str:
    return str(value or "").strip()


def _rule_lookup(name: object, rules: list[tuple[tuple[str, ...], str]], default: str) -> str:
    lower = _normalize_name(name).lower()
    for keywords, label in rules:
        if any(keyword in lower for keyword in keywords):
            return label
    return default


def _amount_series(df: pd.DataFrame) -> pd.Series:
    if "amount" not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)


def _type_series(df: pd.DataFrame) -> pd.Series:
    if "type" not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype=str)
    return df["type"].astype(str).str.upper().fillna("")


def _name_series(df: pd.DataFrame) -> pd.Series:
    if "name" not in df.columns:
        return pd.Series(["Non renseigné"] * len(df), index=df.index, dtype=str)
    return df["name"].fillna("Non renseigné").astype(str)


def _asset_class_series(df: pd.DataFrame) -> pd.Series:
    if "asset_class" not in df.columns:
        return pd.Series(["Non classé"] * len(df), index=df.index, dtype=str)
    return df["asset_class"].fillna("Non classé").astype(str).str.upper()


def _weights_from_flows(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "amount", "weight"])
    grouped = df.groupby(group_col, as_index=False)["exposure_amount"].sum()
    grouped["amount"] = grouped["exposure_amount"].abs()
    total = grouped["amount"].sum()
    grouped["weight"] = grouped["amount"] / total if total else 0.0
    return grouped[[group_col, "amount", "weight"]].sort_values("amount", ascending=False).reset_index(drop=True)


def estimated_position_exposures(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions.copy()
    df["name"] = _name_series(df)
    df["asset_class"] = _asset_class_series(df)
    df["type_norm"] = _type_series(df)
    df["amount_num"] = _amount_series(df)
    # Les achats sont généralement négatifs dans les exports bancaires ; on prend la valeur absolue.
    df["buy_amount"] = df["amount_num"].where(df["type_norm"].eq("BUY"), 0.0).abs()
    df["sell_amount"] = df["amount_num"].where(df["type_norm"].eq("SELL"), 0.0).abs()
    grouped = (
        df.groupby(["name", "asset_class"], as_index=False)
        .agg(buy_amount=("buy_amount", "sum"), sell_amount=("sell_amount", "sum"))
    )
    grouped["net_cost_estimate"] = (grouped["buy_amount"] - grouped["sell_amount"]).clip(lower=0.0)
    grouped = grouped[grouped["net_cost_estimate"] > 0].copy()
    total = grouped["net_cost_estimate"].sum()
    grouped["weight"] = grouped["net_cost_estimate"] / total if total else 0.0
    grouped["sector"] = grouped["name"].map(lambda x: _rule_lookup(x, SECTOR_RULES, "Autres"))
    grouped["geography"] = grouped["name"].map(lambda x: _rule_lookup(x, GEO_RULES, "Autres"))
    grouped["currency"] = grouped["name"].map(lambda x: _rule_lookup(x, CURRENCY_RULES, "Autres"))
    return grouped.sort_values("net_cost_estimate", ascending=False).reset_index(drop=True)


def monthly_evolution(transactions: pd.DataFrame, portfolio_value: float) -> pd.DataFrame:
    if "date" not in transactions.columns:
        return pd.DataFrame(columns=["month", "net_flow", "capital_invested", "estimated_value", "estimated_pnl"])
    df = transactions.dropna(subset=["date"]).copy()
    if df.empty:
        return pd.DataFrame(columns=["month", "net_flow", "capital_invested", "estimated_value", "estimated_pnl"])
    df["type_norm"] = _type_series(df)
    df["amount_num"] = _amount_series(df)
    # Apports/achats nets approximés : achats - ventes - revenus.
    buy = df["amount_num"].where(df["type_norm"].eq("BUY"), 0.0).abs()
    sell = df["amount_num"].where(df["type_norm"].eq("SELL"), 0.0).abs()
    dividends = df["amount_num"].where(df["type_norm"].str.contains("DIVIDEND|INTEREST", regex=True), 0.0).abs()
    df["net_flow"] = buy - sell - dividends
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month", as_index=False)["net_flow"].sum()
    monthly["capital_invested"] = monthly["net_flow"].cumsum().clip(lower=0.0)
    final_invested = float(monthly["capital_invested"].iloc[-1]) if len(monthly) else 0.0
    final_pnl = float(portfolio_value - final_invested)
    if len(monthly) > 1 and final_invested > 0:
        progress = monthly["capital_invested"] / final_invested
        monthly["estimated_value"] = monthly["capital_invested"] + final_pnl * progress
    else:
        monthly["estimated_value"] = portfolio_value
    monthly["estimated_pnl"] = monthly["estimated_value"] - monthly["capital_invested"]
    return monthly


def build_analytics(transactions: pd.DataFrame, net_worth) -> AnalyticsBundle:
    positions = estimated_position_exposures(transactions)
    exposure = positions.rename(columns={"net_cost_estimate": "exposure_amount"}).copy()
    portfolio_value = float(net_worth.total_value or 0.0)

    if not positions.empty and portfolio_value > 0:
        # Rebase les expositions estimées sur la valeur actuelle du portefeuille pour le dashboard.
        positions["estimated_current_value"] = positions["weight"] * portfolio_value
    else:
        positions["estimated_current_value"] = 0.0

    class_alloc = _weights_from_flows(exposure, "asset_class").rename(columns={"asset_class": "Classe d'actifs"})
    sector_alloc = _weights_from_flows(exposure, "sector").rename(columns={"sector": "Secteur"})
    geo_alloc = _weights_from_flows(exposure, "geography").rename(columns={"geography": "Zone"})
    currency_alloc = _weights_from_flows(exposure, "currency").rename(columns={"currency": "Devise"})
    monthly = monthly_evolution(transactions, portfolio_value)
    top = positions[["name", "asset_class", "sector", "geography", "estimated_current_value", "weight"]].head(15).copy()
    return AnalyticsBundle(class_alloc, sector_alloc, geo_alloc, currency_alloc, positions, monthly, top)


def top_label(frame: pd.DataFrame, label_col: str) -> str:
    if frame.empty or label_col not in frame.columns:
        return "—"
    row = frame.iloc[0]
    return f"{row[label_col]} ({row['weight'] * 100:.1f}%)"
