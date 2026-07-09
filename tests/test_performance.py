import pandas as pd

from portfolio_intelligence.imports.trade_republic import summarize_transactions


def test_summarize_transactions():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-01-01", "2026-01-02"]), "type": ["BUY", "SELL"], "amount": [-100.0, 50.0], "fee": [1.0, 1.0]})
    s = summarize_transactions(df)
    assert s.rows == 2
    assert s.buys == 100.0
    assert s.sells == 50.0
    assert s.fees == 2.0
