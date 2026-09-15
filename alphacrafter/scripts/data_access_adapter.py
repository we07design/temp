"""Materialize data_access datasets into AlphaCrafter's CSV contract."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def materialize_daily_csv(
    output_dir: str | Path,
    *,
    dataset: str = "ashare_stock_daily_adj",
    start: str,
    end: str,
    symbols: Iterable[str] | None = None,
) -> int:
    """Read data_access once and write one CSV per instrument.

    The output matches GetStockDataTool, so the existing simulator and agents
    continue to work unchanged.
    """
    from data_access import get_store

    columns = ["TradeDate", "Symbol", "Open", "High", "Low", "Close", "Volume"]
    frame = get_store().read_frame(
        dataset, columns=columns, time_range=(start, end),
        instrument_filter=list(symbols) if symbols else None,
    )
    if frame.empty:
        raise RuntimeError(f"data_access returned no rows for {dataset} {start}:{end}")

    rename = {"TradeDate": "date", "Symbol": "symbol", "Open": "open",
              "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    missing = set(rename) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing data_access columns: {sorted(missing)}")
    frame = frame.rename(columns=rename)
    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    frame["change"] = frame.groupby("symbol")["close"].diff()
    frame["pct_change"] = frame.groupby("symbol")["close"].pct_change() * 100.0
    for col in ("PE", "PS", "PB", "DYR"):
        frame[col] = float("nan")
    out_cols = ["date", "open", "close", "high", "low", "volume",
                "change", "pct_change", "PE", "PS", "PB", "DYR"]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for symbol, group in frame.groupby("symbol", sort=False):
        group.sort_values("date")[out_cols].to_csv(out / f"{symbol}.csv", index=False)
    return int(frame["symbol"].nunique())

