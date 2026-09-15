"""Fetch and cache CSI300 stock daily data for factor mining.

Caches OHLCV + pct_change for the full watchlist into a single pickle file.
Re-run when cache is stale.
"""
import os
import pickle
import pandas as pd
from alphacrafter.sim.utils import get_account_dict, get_stock_daily_data

DAYS = 500
CACHE = "scripts/cache/data.pkl"

def main():
    wl = get_account_dict()["watch_list"]
    data = {}
    ok, fail = 0, 0
    for i, sym in enumerate(wl):
        try:
            df = get_stock_daily_data(sym, days=DAYS)
        except Exception as e:
            df = None
        if df is not None and len(df) > 0:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            data[sym] = df.set_index("date")
            ok += 1
        else:
            fail += 1
    with open(CACHE, "wb") as f:
        pickle.dump(data, f)
    print(f"fetched {ok} stocks, {fail} failed. cached -> {CACHE}")
    # report history length distribution
    lens = sorted(len(d) for d in data.values())
    if lens:
        print("history len: min=%d p10=%d median=%d max=%d" % (
            lens[0], lens[len(lens)//10], lens[len(lens)//2], lens[-1]))

if __name__ == "__main__":
    main()
