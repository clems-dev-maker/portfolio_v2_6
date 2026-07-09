from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from portfolio_intelligence.analytics import estimated_position_exposures


@dataclass(frozen=True)
class LookThroughBundle:
    company_exposure: pd.DataFrame
    sector_exposure: pd.DataFrame
    geography_exposure: pd.DataFrame
    currency_exposure: pd.DataFrame
    theme_exposure: pd.DataFrame
    hidden_concentration: pd.DataFrame


# Modèle look-through volontairement déterministe et local.
# Les pondérations sont des approximations prudentes pour donner une vision consolidée.
# Dans une version ultérieure, elles pourront être remplacées par les CSV officiels des émetteurs.
ETF_HOLDINGS: dict[str, list[dict[str, object]]] = {
    "s&p 500": [
        {"company": "Microsoft", "weight": 0.070, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "NVIDIA", "weight": 0.065, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Apple", "weight": 0.060, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Amazon", "weight": 0.040, "sector": "Consommation discrétionnaire", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Meta Platforms", "weight": 0.030, "sector": "Communication", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Broadcom", "weight": 0.025, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Alphabet", "weight": 0.035, "sector": "Communication", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Autres S&P 500", "weight": 0.675, "sector": "Actions diversifiées", "geography": "États-Unis", "currency": "USD", "theme": "Diversifié"},
    ],
    "nasdaq": [
        {"company": "Microsoft", "weight": 0.085, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "NVIDIA", "weight": 0.075, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Apple", "weight": 0.080, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Amazon", "weight": 0.055, "sector": "Consommation discrétionnaire", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Meta Platforms", "weight": 0.040, "sector": "Communication", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Broadcom", "weight": 0.045, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Tesla", "weight": 0.025, "sector": "Consommation discrétionnaire", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Autres Nasdaq 100", "weight": 0.595, "sector": "Technologie diversifiée", "geography": "États-Unis", "currency": "USD", "theme": "Croissance"},
    ],
    "world quality": [
        {"company": "Microsoft", "weight": 0.055, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Quality / Growth"},
        {"company": "NVIDIA", "weight": 0.045, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Apple", "weight": 0.045, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Quality / Growth"},
        {"company": "Visa", "weight": 0.025, "sector": "Finance", "geography": "États-Unis", "currency": "USD", "theme": "Quality"},
        {"company": "Novo Nordisk", "weight": 0.020, "sector": "Santé", "geography": "Europe", "currency": "DKK", "theme": "Quality"},
        {"company": "ASML", "weight": 0.018, "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "IA / Semi-conducteurs"},
        {"company": "Autres MSCI World Quality", "weight": 0.792, "sector": "Actions qualité diversifiées", "geography": "Monde développé", "currency": "Mixte", "theme": "Quality"},
    ],
    "msci world": [
        {"company": "Microsoft", "weight": 0.045, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "NVIDIA", "weight": 0.040, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Apple", "weight": 0.040, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Amazon", "weight": 0.025, "sector": "Consommation discrétionnaire", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "ASML", "weight": 0.010, "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "IA / Semi-conducteurs"},
        {"company": "Autres MSCI World", "weight": 0.840, "sector": "Actions diversifiées", "geography": "Monde développé", "currency": "Mixte", "theme": "Diversifié"},
    ],
    "semiconductor": [
        {"company": "NVIDIA", "weight": 0.180, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "TSMC", "weight": 0.120, "sector": "Semi-conducteurs", "geography": "Taïwan", "currency": "TWD", "theme": "IA / Semi-conducteurs"},
        {"company": "ASML", "weight": 0.090, "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "IA / Semi-conducteurs"},
        {"company": "Broadcom", "weight": 0.085, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "AMD", "weight": 0.050, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Applied Materials", "weight": 0.045, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Autres semi-conducteurs", "weight": 0.430, "sector": "Semi-conducteurs", "geography": "Monde", "currency": "Mixte", "theme": "IA / Semi-conducteurs"},
    ],
    "information technology": [
        {"company": "Microsoft", "weight": 0.140, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "NVIDIA", "weight": 0.120, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "Apple", "weight": 0.110, "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
        {"company": "Broadcom", "weight": 0.055, "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
        {"company": "ASML", "weight": 0.025, "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "IA / Semi-conducteurs"},
        {"company": "Autres technologie", "weight": 0.550, "sector": "Technologie diversifiée", "geography": "Monde développé", "currency": "Mixte", "theme": "Technologie"},
    ],
    "europe growth": [
        {"company": "ASML", "weight": 0.070, "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "Quality / Growth"},
        {"company": "Novo Nordisk", "weight": 0.060, "sector": "Santé", "geography": "Europe", "currency": "DKK", "theme": "Quality / Growth"},
        {"company": "LVMH", "weight": 0.035, "sector": "Luxe", "geography": "Europe", "currency": "EUR", "theme": "Luxe"},
        {"company": "Hermès", "weight": 0.030, "sector": "Luxe", "geography": "Europe", "currency": "EUR", "theme": "Luxe"},
        {"company": "SAP", "weight": 0.030, "sector": "Technologie", "geography": "Europe", "currency": "EUR", "theme": "Quality / Growth"},
        {"company": "Autres Europe Growth", "weight": 0.775, "sector": "Actions Europe croissance", "geography": "Europe", "currency": "EUR", "theme": "Quality / Growth"},
    ],
    "emerging": [
        {"company": "TSMC", "weight": 0.090, "sector": "Semi-conducteurs", "geography": "Taïwan", "currency": "TWD", "theme": "IA / Semi-conducteurs"},
        {"company": "Tencent", "weight": 0.040, "sector": "Communication", "geography": "Chine", "currency": "HKD", "theme": "Emerging Growth"},
        {"company": "Alibaba", "weight": 0.030, "sector": "Consommation discrétionnaire", "geography": "Chine", "currency": "HKD", "theme": "Emerging Growth"},
        {"company": "Samsung Electronics", "weight": 0.035, "sector": "Semi-conducteurs", "geography": "Corée du Sud", "currency": "KRW", "theme": "IA / Semi-conducteurs"},
        {"company": "Autres émergents", "weight": 0.805, "sector": "Actions émergentes diversifiées", "geography": "Émergents", "currency": "Mixte", "theme": "Emerging Markets"},
    ],
    "japan": [
        {"company": "Toyota", "weight": 0.045, "sector": "Industrie / Automobile", "geography": "Japon", "currency": "JPY", "theme": "Japon"},
        {"company": "Sony", "weight": 0.030, "sector": "Technologie", "geography": "Japon", "currency": "JPY", "theme": "Japon"},
        {"company": "Tokyo Electron", "weight": 0.025, "sector": "Semi-conducteurs", "geography": "Japon", "currency": "JPY", "theme": "IA / Semi-conducteurs"},
        {"company": "Autres Japon", "weight": 0.900, "sector": "Actions Japon diversifiées", "geography": "Japon", "currency": "JPY", "theme": "Japon"},
    ],
}

DIRECT_COMPANY_META: dict[str, dict[str, str]] = {
    "nvidia": {"company": "NVIDIA", "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
    "asml": {"company": "ASML", "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "IA / Semi-conducteurs"},
    "micron": {"company": "Micron Technology", "sector": "Semi-conducteurs", "geography": "États-Unis", "currency": "USD", "theme": "IA / Semi-conducteurs"},
    "semiconductor inds": {"company": "BE Semiconductor", "sector": "Semi-conducteurs", "geography": "Europe", "currency": "EUR", "theme": "IA / Semi-conducteurs"},
    "applied optoelectronics": {"company": "Applied Optoelectronics", "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "IA / Infrastructure"},
    "applied digital": {"company": "Applied Digital", "sector": "Technologie", "geography": "États-Unis", "currency": "USD", "theme": "IA / Infrastructure"},
    "amazon": {"company": "Amazon", "sector": "Consommation discrétionnaire", "geography": "États-Unis", "currency": "USD", "theme": "Magnificent 7"},
    "hermes": {"company": "Hermès", "sector": "Luxe", "geography": "Europe", "currency": "EUR", "theme": "Luxe"},
    "lotus": {"company": "Lotus Bakeries", "sector": "Consommation de base", "geography": "Europe", "currency": "EUR", "theme": "Quality"},
    "abb": {"company": "ABB", "sector": "Industrie", "geography": "Europe", "currency": "CHF", "theme": "Électrification"},
    "exail": {"company": "Exail Technologies", "sector": "Industrie / Défense", "geography": "Europe", "currency": "EUR", "theme": "Défense"},
    "lynas": {"company": "Lynas Rare Earths", "sector": "Matières stratégiques", "geography": "Australie", "currency": "AUD", "theme": "Métaux stratégiques"},
    "amgen": {"company": "Amgen", "sector": "Santé", "geography": "États-Unis", "currency": "USD", "theme": "Santé"},
    "intuitive": {"company": "Intuitive Surgical", "sector": "Santé", "geography": "États-Unis", "currency": "USD", "theme": "Santé"},
    "viking": {"company": "Viking Therapeutics", "sector": "Biotechnologie", "geography": "États-Unis", "currency": "USD", "theme": "Santé"},
    "gaztransport": {"company": "Gaztransport & Technigaz", "sector": "Énergie", "geography": "Europe", "currency": "EUR", "theme": "Énergie"},
    "coinbase": {"company": "Coinbase", "sector": "Crypto / Finance", "geography": "États-Unis", "currency": "USD", "theme": "Crypto"},
}


def _match_etf_model(name: str) -> list[dict[str, object]] | None:
    lower = name.lower()
    for key, holdings in ETF_HOLDINGS.items():
        if key in lower:
            return holdings
    return None


def _direct_meta(name: str, asset_class: str) -> dict[str, str]:
    lower = name.lower()
    for key, meta in DIRECT_COMPANY_META.items():
        if key in lower:
            return meta
    if "bitcoin" in lower or "ethereum" in lower or "solana" in lower or "cardano" in lower or asset_class.upper() == "CRYPTO":
        return {"company": name, "sector": "Crypto", "geography": "Décentralisé", "currency": "Crypto", "theme": "Crypto"}
    if "gold" in lower or "silver" in lower or "palladium" in lower:
        return {"company": name, "sector": "Métaux précieux", "geography": "Monde", "currency": "USD", "theme": "Métaux précieux"}
    if "bond" in lower or "dez." in lower or "aug." in lower or "sept." in lower:
        return {"company": name, "sector": "Obligations", "geography": "Mixte", "currency": "Mixte", "theme": "Obligations"}
    return {"company": name, "sector": "Autres", "geography": "Autres", "currency": "Autres", "theme": "Autres"}


def _allocation(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "amount", "weight"])
    grouped = df.groupby(group_col, as_index=False)["lookthrough_value"].sum()
    grouped = grouped.rename(columns={"lookthrough_value": "amount"})
    total = grouped["amount"].sum()
    grouped["weight"] = grouped["amount"] / total if total else 0.0
    return grouped.sort_values("amount", ascending=False).reset_index(drop=True)


def build_lookthrough(transactions: pd.DataFrame, net_worth) -> LookThroughBundle:
    positions = estimated_position_exposures(transactions)
    portfolio_value = float(getattr(net_worth, "total_value", 0.0) or 0.0)
    if positions.empty:
        empty = pd.DataFrame(columns=["company", "amount", "weight"])
        return LookThroughBundle(empty, empty, empty, empty, empty, empty)

    rows: list[dict[str, object]] = []
    for _, pos in positions.iterrows():
        name = str(pos.get("name", ""))
        asset_class = str(pos.get("asset_class", ""))
        position_value = float(pos.get("weight", 0.0) or 0.0) * portfolio_value
        # Les ETF à levier sont traités en notionnel pour visualiser l'exposition économique.
        leverage = 2.0 if "2x" in name.lower() or "leveraged" in name.lower() else 1.0
        model = _match_etf_model(name)
        if model:
            for holding in model:
                h_weight = float(holding["weight"])
                rows.append({
                    "source_position": name,
                    "company": holding["company"],
                    "sector": holding["sector"],
                    "geography": holding["geography"],
                    "currency": holding["currency"],
                    "theme": holding["theme"],
                    "source_value": position_value,
                    "holding_weight": h_weight,
                    "lookthrough_value": position_value * leverage * h_weight,
                    "leverage_factor": leverage,
                    "mode": "ETF look-through",
                })
        else:
            meta = _direct_meta(name, asset_class)
            rows.append({
                "source_position": name,
                "company": meta["company"],
                "sector": meta["sector"],
                "geography": meta["geography"],
                "currency": meta["currency"],
                "theme": meta["theme"],
                "source_value": position_value,
                "holding_weight": 1.0,
                "lookthrough_value": position_value,
                "leverage_factor": leverage,
                "mode": "Direct / non modélisé",
            })

    detail = pd.DataFrame(rows)
    company = _allocation(detail, "company").rename(columns={"company": "Société"})
    sector = _allocation(detail, "sector").rename(columns={"sector": "Secteur réel"})
    geography = _allocation(detail, "geography").rename(columns={"geography": "Zone réelle"})
    currency = _allocation(detail, "currency").rename(columns={"currency": "Devise réelle"})
    theme = _allocation(detail, "theme").rename(columns={"theme": "Thème"})
    hidden = (
        detail.groupby("company", as_index=False)
        .agg(sources=("source_position", lambda x: ", ".join(sorted(set(map(str, x)))[:5])), amount=("lookthrough_value", "sum"))
        .sort_values("amount", ascending=False)
        .reset_index(drop=True)
    )
    total = hidden["amount"].sum()
    hidden["weight"] = hidden["amount"] / total if total else 0.0
    hidden = hidden.rename(columns={"company": "Société", "sources": "Sources"})
    return LookThroughBundle(company, sector, geography, currency, theme, hidden)


def lookthrough_value(frame: pd.DataFrame, label_col: str) -> str:
    if frame.empty or label_col not in frame.columns:
        return "—"
    row = frame.iloc[0]
    return f"{row[label_col]} ({row['weight'] * 100:.1f}%)"
