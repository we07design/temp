"""Run factor_engine DSL factors against a data_access-backed source."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class DataAccessSeriesSource:
    """FactorEngine DataSource implemented with data_access.read_frame."""
    def __init__(self, dataset: str, start: str, end: str, symbols=None):
        self.dataset, self.start, self.end = dataset, start, end
        self.symbols = list(symbols) if symbols else None
        self._cache: dict[str, pd.Series] = {}

    def load_column(self, name: str):
        if name in self._cache:
            return self._cache[name]
        from data_access import get_store
        df = get_store().read_frame(
            self.dataset,
            columns=["TradeDate", "Symbol", name],
            time_range=(self.start, self.end),
            instrument_filter=self.symbols,
        )
        df["TradeDate"] = pd.to_datetime(df["TradeDate"])
        series = df.set_index(["TradeDate", "Symbol"])[name].sort_index()
        self._cache[name] = series
        return series


def run_dsl_factor(expression: str, *, name: str, start: str, end: str,
                   dataset: str = "ashare_stock_daily_adj", symbols=None,
                   output_dir: str | Path | None = None) -> dict[str, Any]:
    from factor_engine.api.dsl_parser import parse_factor
    from factor_engine.backend.pandas_backend import PandasBackend
    from factor_engine.runtime.engine import FactorEngine

    factor = parse_factor(expression, name=name)
    engine = FactorEngine(
        backend=PandasBackend(),
        data_source=DataAccessSeriesSource(dataset, start, end, symbols),
    )
    result = engine.run(factor)
    values = result["result"]
    if isinstance(values, pd.Series):
        values = values.rename("value").reset_index()
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        payload = {
            "factor_name": name,
            "description": "factor_engine factor",
            "calculation": {"expression": expression},
            "data": values.to_dict(orient="records"),
            "metadata": {"source": "factor_engine", "dataset": dataset,
                         "start": start, "end": end},
        }
        import json
        (out / f"{name}.json").write_text(json.dumps(payload, default=str), encoding="utf-8")
    return {"factor": factor, "result": values, "analysis": result.get("analysis")}

