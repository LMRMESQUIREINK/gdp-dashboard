"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Strategy: 10X multi-symbol / walk-forward / risk-         ║
║                 adjusted / attempt-tracked / cost-stressed     ║
║      Symbol(s): configurable basket (default: NVDA, AAPL, KO)  ║
║      Timeframe: daily                                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

SETUP
    pip install vectorbt==0.28.5 yfinance "pandas>=2.0.0,<3.0.0" numpy --break-system-packages
    (pandas must stay < 3.0 — same constraint as the original product)

Usage:
    python run_10x.py
    python run_10x.py --symbols NVDA AAPL KO --size 2 --min-sharpe 0.7
"""

import argparse

from data_pipeline_10x import fetch_basket
from strategy_generator_10x import Generator10X, SearchConfig


def main():
    parser = argparse.ArgumentParser(description="RUTHLESS 10X Strategy Generator")
    parser.add_argument("--symbols", nargs="+", default=["NVDA", "AAPL", "KO"],
                         help="Basket of tickers — deliberately mixed regimes by default "
                              "(growth mega-cap, growth mega-cap, defensive consumer staple)")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--size", type=int, default=1, help="Conditions combined per entry/exit")
    parser.add_argument("--min-sharpe", type=float, default=0.5)
    parser.add_argument("--max-attempts", type=int, default=20_000)
    args = parser.parse_args()

    print(f"♛ RUTHLESS 10X — fetching basket: {args.symbols}\n")
    frames = fetch_basket(args.symbols, args.start, args.end)

    cfg = SearchConfig(size=args.size, min_sharpe=args.min_sharpe,
                        max_attempts=args.max_attempts)
    gen = Generator10X(frames, config=cfg)

    # NOTE: this counts distinct column-NAME prefixes, which comes out to 14
    # (OBV/VWAP and Zscore/ROC are one conceptual "family" each in
    # conditions.py but use two different name prefixes) — not the 12
    # conceptual indicator families described in README_10X.md. Both
    # numbers are real; this one is just more granular. See README_10X.md.
    print(f"♛ Condition library: {len(gen.all_columns)} conditions across "
          f"{len(set(c.split('_')[0] for c in gen.all_columns))} name-prefixes "
          f"(12 conceptual indicator families)\n")

    result = gen.search(verbose=True)

    print("\n♛ ═══════════════════════════════════════════════════════")
    print("♛ RESULT — survived multi-symbol walk-forward + cost stress")
    print("♛ ═══════════════════════════════════════════════════════")
    print(f"  Attempts tried before this passed : {result.attempts_tried}")
    print(f"  Symbols validated on               : {result.symbols_validated}")
    print(f"  Entry conditions                   : {result.entry}")
    print(f"  Exit conditions                    : {result.exit_}")
    print(f"  Cost-stress test                   : "
          f"{'PASSED' if result.stress_test_passed else 'FAILED'} "
          f"(min Sharpe under stress = {result.stress_sharpe})")
    print("\n  Per-fold Sharpe (IS / OOS), by symbol:")
    for fold in result.fold_stats:
        print(f"    {fold['symbol']}: IS Sharpe={fold['is_sharpe']}, "
              f"OOS Sharpe={fold['oos_sharpe']}")
    print("\n  ⚠ This is still a research prototype, not trading advice — see README_10X.md.")


if __name__ == "__main__":
    main()
