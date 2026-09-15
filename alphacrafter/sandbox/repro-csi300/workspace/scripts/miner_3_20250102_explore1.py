"""Exploration cycle 1 (2025-01-02): batch-test classic candidate factors.

Each candidate is validated independently across 1d and 5d horizons.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd
from miner_3_common import load_data, validate_factor, print_results

print("Loading data ...")
data = load_data(min_days=300)
print(f"Loaded {len(data)} symbols")

# ---------- Candidate factors ----------
candidates = {}

# 1. Short-term reversal: negative of 5-day return
candidates["reversal_5d"] = lambda d: -(d["close"].pct_change(5))

# 2. Medium-term momentum: 60-day return
candidates["momentum_60d"] = lambda d: d["close"].pct_change(60)

# 3. 20-day momentum
candidates["momentum_20d"] = lambda d: d["close"].pct_change(20)

# 4. Volatility (low-vol): negative 20d std of returns
candidates["lowvol_20d"] = lambda d: -(d["close"].pct_change().rolling(20).std())

# 5. Volume-ratio reversal: 5d return * volume change
candidates["vol_adj_rev"] = lambda d: -(d["close"].pct_change(5)) * (d["volume"].rolling(5).mean() / d["volume"].rolling(20).mean())

# 6. Distance from 20d MA (mean reversion)
candidates["ma_dist_20d"] = lambda d: -(d["close"] / d["close"].rolling(20).mean() - 1)

# 7. Amihud illiquidity (negative, liquidity premium): |ret|/volume
candidates["illiquidity"] = lambda d: (d["close"].pct_change().abs() / (d["volume"] + 1)).rolling(20).mean()

# 8. Turnover proxy: volume / 20d avg volume
candidates["volume_surge"] = lambda d: -(d["volume"].rolling(5).mean() / d["volume"].rolling(20).mean())

results_all = {}
for name, fn in candidates.items():
    try:
        res = validate_factor(data, fn, name)
        ok = print_results(name, res)
        results_all[name] = ok
    except Exception as e:
        print(f"ERROR in {name}: {e}")

print("\n=== SUMMARY ===")
for k, v in results_all.items():
    print(f"{k}: {'PASS' if v else 'FAIL'}")
