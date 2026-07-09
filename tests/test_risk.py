import pandas as pd

from portfolio_intelligence.risk.engine import build_risk
from portfolio_intelligence.imports.net_worth_pdf import NetWorth
from portfolio_intelligence.performance.metrics import DashboardMetrics


def test_risk_bundle_has_summary():
    tx = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "type": ["BUY", "BUY"],
        "asset_class": ["STOCK", "FUND"],
        "name": ["NVIDIA", "Core S&P 500"],
        "amount": [-100.0, -200.0],
    })
    metrics = DashboardMetrics(300.0, 300.0, 0.0, 0.0, 2, 2, "2026-01-01", "2026-01-02", 0.0, 0.0, 0.0)
    risk = build_risk(tx, NetWorth(300.0), metrics)
    assert not risk.summary.empty
    assert "VaR 95% mensuelle" in set(risk.summary["Indicateur"])
