from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TransactionSummary:
    rows: int
    first_date: str | None
    last_date: str | None
    buys: float
    sells: float
    dividends: float
    interests: float
    fees: float


def load_transactions(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV introuvable : {path}")
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["amount", "fee", "shares", "price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def summarize_transactions(df: pd.DataFrame) -> TransactionSummary:
    type_col = "type" if "type" in df.columns else None
    cat_col = "category" if "category" in df.columns else None
    amount = df["amount"] if "amount" in df.columns else pd.Series([0.0] * len(df))
    fee = df["fee"] if "fee" in df.columns else pd.Series([0.0] * len(df))
    types = df[type_col].astype(str).str.upper() if type_col else pd.Series([""] * len(df))
    cats = df[cat_col].astype(str).str.upper() if cat_col else pd.Series([""] * len(df))

    buys = abs(amount[types.eq("BUY")].sum())
    sells = abs(amount[types.eq("SELL")].sum())
    dividends = amount[types.str.contains("DIVIDEND", na=False) | cats.str.contains("DIVIDEND", na=False)].sum()
    interests = amount[types.str.contains("INTEREST", na=False) | cats.str.contains("INTEREST", na=False)].sum()
    fees = abs(fee.sum())
    first = None
    last = None
    if "date" in df.columns and not df["date"].dropna().empty:
        first = df["date"].min().date().isoformat()
        last = df["date"].max().date().isoformat()
    return TransactionSummary(len(df), first, last, float(buys), float(sells), float(dividends), float(interests), float(fees))
