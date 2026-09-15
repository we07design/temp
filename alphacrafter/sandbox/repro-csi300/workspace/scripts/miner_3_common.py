"""Shared utilities for factor mining / validation (miner_3)."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from alphacrafter.sim.utils import get_account_dict, get_stock_daily_data

HORIZONS = [1, 5]
MIN_REQUIRED_DAYS = 300  # need enough history


def load_data(min_days=MIN_REQUIRED_DAYS, max_stocks=None):
    """Load close/volume/open/high/low panels for the watchlist.

    Returns dict: symbol -> DataFrame indexed by date with columns:
      close, open, high, low, volume, return_1d, return_5d
    """
    universe = get_account_dict()["watch_list"]
    if max_stocks:
        universe = universe[:max_stocks]
    data = {}
    for sym in universe:
        df = get_stock_daily_data(sym, days=min_days)
        if df is None or len(df) < min_days:
            continue
        d = df.copy()
        d = d.sort_values("date").reset_index(drop=True)
        d = d.set_index("date")
        d = d[["open", "close", "high", "low", "volume"]].astype(float)
        d["return_1d"] = d["close"].pct_change(1).shift(-1)
        d["return_5d"] = d["close"].pct_change(5).shift(-5)
        data[sym] = d
    return data


def validate_factor(data, factor_fn, factor_name="factor"):
    """Compute metrics across horizons for a factor.

    factor_fn(d) -> pd.Series (indexed by date) of factor values for symbol d.
    Returns dict of metrics per horizon.
    """
    # attach factor values
    factors = {}
    for sym, d in data.items():
        f = factor_fn(d)
        f = pd.Series(f, index=d.index) if not isinstance(f, pd.Series) else f
        factors[sym] = f

    results = {}
    for h in HORIZONS:
        ret_col = f"return_{h}d"
        dates = sorted(set().union(*[d.index for d in data.values()]))
        ic_list, rank_ic_list, cov_list, turn_list = [], [], [], []
        prev_rank = None
        for t in dates:
            fv, rv, syms = [], [], []
            for sym, d in data.items():
                if t in d.index and t in factors[sym].index:
                    f = factors[sym].loc[t]
                    r = d.loc[t, ret_col]
                    if pd.notna(f) and pd.notna(r) and np.isfinite(f):
                        fv.append(f); rv.append(r); syms.append(sym)
            n_total = len(data)
            cov_list.append(len(fv) / n_total if n_total else 0.0)
            if len(fv) >= 30 and np.std(fv) > 0:
                ic = np.corrcoef(fv, rv)[0, 1]
                ric, _ = spearmanr(fv, rv)
                if np.isfinite(ic):
                    ic_list.append(ic)
                if np.isfinite(ric):
                    rank_ic_list.append(ric)
                curr_rank = pd.Series(fv, index=syms).rank()
                if prev_rank is not None:
                    a = curr_rank.align(prev_rank, join="inner")
                    if len(a[0]) > 0:
                        turn_list.append(np.abs(a[0] - a[1]).sum() / len(a[0]))
                prev_rank = curr_rank
        ic_mean = np.mean(ic_list) if ic_list else 0.0
        ric_mean = np.mean(rank_ic_list) if rank_ic_list else 0.0
        icir = ic_mean / np.std(ic_list) if ic_list and np.std(ic_list) > 0 else 0.0
        ricir = ric_mean / np.std(rank_ic_list) if rank_ic_list and np.std(rank_ic_list) > 0 else 0.0
        hit = np.mean([1 for v in rank_ic_list if v > 0]) if rank_ic_list else 0.0
        cov = np.mean(cov_list) if cov_list else 0.0
        turn = np.mean(turn_list) if turn_list else 0.0
        results[h] = dict(IC=ic_mean, RankIC=ric_mean, ICIR=icir, RankICIR=ricir,
                          HitRatio=hit, Coverage=cov, Turnover=turn, n_ic=len(ic_list))
    return results


def print_results(name, results):
    print(f"=== FACTOR: {name} ===")
    ok = True
    thresholds = {1: dict(IC=0.015, RankIC=0.015, ICIR=0.2, RankICIR=0.2, hit_lo=0.4, hit_hi=0.6, cov=0.9, turn=0.4),
                  5: dict(IC=0.025, RankIC=0.025, ICIR=0.25, RankICIR=0.25, hit_lo=0.4, hit_hi=0.6, cov=0.9, turn=0.4)}
    for h in HORIZONS:
        r = results[h]
        th = thresholds[h]
        passed = (
            abs(r['IC']) > th['IC'] and abs(r['RankIC']) > th['RankIC'] and
            abs(r['ICIR']) > th['ICIR'] and abs(r['RankICIR']) > th['RankICIR'] and
            (r['HitRatio'] > th['hit_hi'] or r['HitRatio'] < th['hit_lo']) and
            r['Coverage'] > th['cov'] and r['Turnover'] < th['turn']
        )
        ok = ok and passed
        print(f"  H={h}d: IC={r['IC']:.4f} RankIC={r['RankIC']:.4f} ICIR={r['ICIR']:.4f} "
              f"RankICIR={r['RankICIR']:.4f} Hit={r['HitRatio']:.4f} Cov={r['Coverage']:.4f} "
              f"Turn={r['Turnover']:.4f} nIC={r['n_ic']} -> {'PASS' if passed else 'FAIL'}")
    print(f"  OVERALL: {'PASS' if ok else 'FAIL'}")
    return ok
