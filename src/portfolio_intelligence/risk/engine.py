
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from portfolio_intelligence.analytics import build_analytics

RISK_FREE_RATE = 0.025

VOL_RULES: list[tuple[tuple[str, ...], float]] = [
    (("bitcoin", "ethereum", "solana", "cardano", "crypto", "coinbase"), 0.75),
    (("nasdaq", "2x", "leveraged", "daily"), 0.42),
    (("nvidia", "asml", "semiconductor", "semi", "micron", "applied materials", "besi", "optoelectronics", "digital"), 0.38),
    (("solar", "uranium", "nuclear", "rare earth", "lynas", "mining"), 0.36),
    (("gold", "silver", "palladium", "physical"), 0.23),
    (("hermes", "lotus", "amazon", "viking", "intuitive"), 0.30),
    (("msci", "s&p", "sp 500", "world", "euro stoxx", "core"), 0.20),
    (("bond", "ibonds", "dez.", "aug.", "sept."), 0.07),
]

EXPECTED_RETURN_RULES: list[tuple[tuple[str, ...], float]] = [
    (("bitcoin", "ethereum", "solana", "cardano", "crypto"), 0.10),
    (("nasdaq", "2x", "leveraged", "daily"), 0.08),
    (("nvidia", "asml", "semiconductor", "semi", "micron", "applied materials", "besi"), 0.09),
    (("gold", "silver", "palladium", "physical"), 0.04),
    (("bond", "ibonds", "dez.", "aug.", "sept."), 0.03),
    (("msci", "s&p", "sp 500", "world", "euro stoxx", "core"), 0.065),
]

STRESS_SCENARIOS: dict[str, dict[str, float]] = {
    "Crise financière 2008": {
        "ETF actions diversifiés": -0.38,
        "Technologie / Semi-conducteurs": -0.45,
        "Consommation / Luxe": -0.35,
        "Santé": -0.22,
        "Industrie / Matières stratégiques": -0.40,
        "Énergie": -0.42,
        "Métaux précieux": -0.08,
        "Crypto": -0.60,
        "Obligations": 0.06,
        "Autres": -0.25,
    },
    "COVID-2020": {
        "ETF actions diversifiés": -0.30,
        "Technologie / Semi-conducteurs": -0.28,
        "Consommation / Luxe": -0.34,
        "Santé": -0.18,
        "Industrie / Matières stratégiques": -0.33,
        "Énergie": -0.48,
        "Métaux précieux": -0.04,
        "Crypto": -0.45,
        "Obligations": 0.03,
        "Autres": -0.25,
    },
    "Bear market 2022 / taux": {
        "ETF actions diversifiés": -0.22,
        "Technologie / Semi-conducteurs": -0.36,
        "Consommation / Luxe": -0.24,
        "Santé": -0.14,
        "Industrie / Matières stratégiques": -0.18,
        "Énergie": 0.10,
        "Métaux précieux": -0.02,
        "Crypto": -0.65,
        "Obligations": -0.12,
        "Autres": -0.18,
    },
    "Choc semi-conducteurs": {
        "ETF actions diversifiés": -0.12,
        "Technologie / Semi-conducteurs": -0.45,
        "Consommation / Luxe": -0.12,
        "Santé": -0.06,
        "Industrie / Matières stratégiques": -0.18,
        "Énergie": -0.06,
        "Métaux précieux": 0.03,
        "Crypto": -0.25,
        "Obligations": 0.02,
        "Autres": -0.10,
    },
    "Dollar -20%": {
        "ETF actions diversifiés": -0.10,
        "Technologie / Semi-conducteurs": -0.12,
        "Consommation / Luxe": -0.04,
        "Santé": -0.08,
        "Industrie / Matières stratégiques": -0.04,
        "Énergie": -0.06,
        "Métaux précieux": 0.08,
        "Crypto": -0.08,
        "Obligations": 0.00,
        "Autres": -0.04,
    },
    "Crise Taïwan": {
        "ETF actions diversifiés": -0.28,
        "Technologie / Semi-conducteurs": -0.55,
        "Consommation / Luxe": -0.25,
        "Santé": -0.15,
        "Industrie / Matières stratégiques": -0.28,
        "Énergie": 0.10,
        "Métaux précieux": 0.12,
        "Crypto": -0.35,
        "Obligations": 0.03,
        "Autres": -0.20,
    },
}


@dataclass(frozen=True)
class RiskBundle:
    summary: pd.DataFrame
    risk_by_position: pd.DataFrame
    concentration: pd.DataFrame
    stress_tests: pd.DataFrame
    alerts: pd.DataFrame
    correlation_matrix: pd.DataFrame


def _lookup(name: str, rules: list[tuple[tuple[str, ...], float]], default: float) -> float:
    lower = str(name or "").lower()
    for keywords, value in rules:
        if any(k in lower for k in keywords):
            return value
    return default


def _sector_corr(a: str, b: str) -> float:
    if a == b:
        return 1.0
    cyclical = {"ETF actions diversifiés", "Technologie / Semi-conducteurs", "Consommation / Luxe", "Industrie / Matières stratégiques", "Énergie"}
    defensive = {"Métaux précieux", "Obligations"}
    if a in cyclical and b in cyclical:
        return 0.72
    if a in defensive and b in defensive:
        return 0.20
    if "Crypto" in (a, b):
        return 0.45 if (a in cyclical or b in cyclical) else 0.25
    if a in defensive or b in defensive:
        return 0.10
    return 0.45


def _z(confidence: float) -> float:
    if confidence >= 0.99:
        return 2.326
    if confidence >= 0.975:
        return 1.960
    return 1.645


def _expected_shortfall_z(confidence: float) -> float:
    # E[loss | loss > VaR] coefficient for a normal distribution.
    # phi(z)/(1-alpha), with common approximations to avoid scipy dependency.
    z = _z(confidence)
    phi = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return phi / (1.0 - confidence)


def build_risk(transactions: pd.DataFrame, net_worth, metrics) -> RiskBundle:
    analytics = build_analytics(transactions, net_worth)
    positions = analytics.positions_estimated.copy()
    portfolio_value = float(getattr(net_worth, "total_value", 0.0) or 0.0)
    if positions.empty or portfolio_value <= 0:
        empty = pd.DataFrame()
        return RiskBundle(empty, empty, empty, empty, empty, empty)

    if "estimated_current_value" not in positions.columns:
        positions["estimated_current_value"] = positions["weight"] * portfolio_value
    positions["risk_volatility"] = positions["name"].map(lambda x: _lookup(x, VOL_RULES, 0.26))
    positions["expected_return"] = positions["name"].map(lambda x: _lookup(x, EXPECTED_RETURN_RULES, 0.06))

    weights = positions["weight"].to_numpy(dtype=float)
    vols = positions["risk_volatility"].to_numpy(dtype=float)
    sectors = positions["sector"].astype(str).tolist()
    n = len(positions)
    corr = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            corr[i, j] = corr[j, i] = _sector_corr(sectors[i], sectors[j])
    cov = np.outer(vols, vols) * corr
    variance = float(weights @ cov @ weights.T)
    portfolio_vol = math.sqrt(max(variance, 0.0))
    marginal = cov @ weights
    risk_contribution = weights * marginal / portfolio_vol if portfolio_vol > 0 else np.zeros(n)
    risk_contribution_pct = risk_contribution / portfolio_vol if portfolio_vol > 0 else np.zeros(n)
    expected_return = float(np.dot(weights, positions["expected_return"].to_numpy(dtype=float)))
    sharpe = (expected_return - RISK_FREE_RATE) / portfolio_vol if portfolio_vol else 0.0
    var95 = portfolio_value * portfolio_vol * _z(0.95) / math.sqrt(12)
    cvar95 = portfolio_value * portfolio_vol * _expected_shortfall_z(0.95) / math.sqrt(12)
    max_drawdown_est = min(0.95, portfolio_vol * 1.75)
    hhi = float(np.sum(weights ** 2) * 10000)
    effective_positions = float(1.0 / np.sum(weights ** 2)) if np.sum(weights ** 2) > 0 else 0.0
    top5 = float(np.sort(weights)[-5:].sum()) if n >= 5 else float(weights.sum())
    top10 = float(np.sort(weights)[-10:].sum()) if n >= 10 else float(weights.sum())

    summary = pd.DataFrame([
        ["Volatilité annualisée estimée", portfolio_vol],
        ["Rendement attendu annualisé", expected_return],
        ["Sharpe estimé", sharpe],
        ["VaR 95% mensuelle", var95],
        ["CVaR 95% mensuelle", cvar95],
        ["Drawdown maximal estimé", max_drawdown_est],
        ["HHI concentration", hhi],
        ["Nombre effectif de positions", effective_positions],
        ["Top 5 positions", top5],
        ["Top 10 positions", top10],
    ], columns=["Indicateur", "Valeur"])

    risk_by_position = positions[["name", "asset_class", "sector", "geography", "estimated_current_value", "weight", "risk_volatility"]].copy()
    risk_by_position["risk_contribution_pct"] = risk_contribution_pct
    risk_by_position["risk_contribution_value"] = risk_contribution_pct * portfolio_value
    risk_by_position = risk_by_position.sort_values("risk_contribution_pct", ascending=False).reset_index(drop=True)

    concentration = pd.DataFrame([
        ["Top 5", top5],
        ["Top 10", top10],
        ["HHI", hhi],
        ["Nombre effectif", effective_positions],
        ["Plus grosse ligne", float(weights.max())],
    ], columns=["Mesure", "Valeur"])

    sector_weights = positions.groupby("sector", as_index=False)["weight"].sum()
    stresses = []
    for scenario, shocks in STRESS_SCENARIOS.items():
        impact_pct = 0.0
        for _, row in sector_weights.iterrows():
            impact_pct += float(row["weight"]) * shocks.get(str(row["sector"]), shocks.get("Autres", -0.15))
        stresses.append([scenario, impact_pct, impact_pct * portfolio_value])
    stress_tests = pd.DataFrame(stresses, columns=["Scénario", "Impact %", "Impact €"])

    alerts = []
    def add_alert(level: str, message: str, value: float | None = None) -> None:
        alerts.append([level, message, value])
    if hhi > 1000:
        add_alert("Orange", "Concentration HHI élevée", hhi)
    if top10 > 0.60:
        add_alert("Orange", "Top 10 supérieur à 60% du portefeuille", top10)
    tech_weight = float(sector_weights.loc[sector_weights["sector"].eq("Technologie / Semi-conducteurs"), "weight"].sum())
    if tech_weight > 0.20:
        add_alert("Orange", "Exposition semi-conducteurs/technologie élevée", tech_weight)
    crypto_weight = float(sector_weights.loc[sector_weights["sector"].eq("Crypto"), "weight"].sum())
    if crypto_weight > 0.08:
        add_alert("Orange", "Exposition crypto élevée", crypto_weight)
    if portfolio_vol > 0.25:
        add_alert("Orange", "Volatilité estimée élevée", portfolio_vol)
    if not alerts:
        add_alert("Vert", "Aucune alerte majeure selon les seuils v2.3", None)
    alerts_df = pd.DataFrame(alerts, columns=["Niveau", "Alerte", "Valeur"])

    labels = positions["name"].astype(str).head(20).tolist()
    corr_df = pd.DataFrame(corr[:len(labels), :len(labels)], index=labels, columns=labels)
    return RiskBundle(summary, risk_by_position, concentration, stress_tests, alerts_df, corr_df)


def risk_value(summary: pd.DataFrame, indicator: str, default: float = 0.0) -> float:
    if summary.empty:
        return default
    row = summary.loc[summary["Indicateur"].eq(indicator)]
    if row.empty:
        return default
    try:
        return float(row.iloc[0]["Valeur"])
    except Exception:
        return default
