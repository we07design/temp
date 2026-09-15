#!/usr/bin/env python
import argparse
from data_access_adapter import materialize_daily_csv

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--start", required=True)
parser.add_argument("--end", required=True)
parser.add_argument("--dataset", default="ashare_stock_daily_adj")
parser.add_argument("--symbols", nargs="*")
args = parser.parse_args()
count = materialize_daily_csv(args.output, dataset=args.dataset, start=args.start,
                              end=args.end, symbols=args.symbols)
print(f"materialized {count} instruments into {args.output}")

