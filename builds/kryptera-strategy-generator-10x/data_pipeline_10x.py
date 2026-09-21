"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: data_pipeline_10x.py                          ║
║      Role:      Multi-symbol yfinance fetch (kept on yfinance  ║
║                  to match the original Kryptera product)       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Named and imported by run_10x.py as `fetch_basket` per README_10X.md's
own file table, but never uploaded — same "core file referenced, never
included" pattern as conditions.py and every other round of this build.
Written here to match run_10x.py's actual call signature exactly:
`fetch_basket(args.symbols, args.start, args.end)`.
"""

import pandas as pd


def fetch_basket(symbols: list, start: str, end: str, interval: str = "1d") -> dict:
    """
    Fetch OHLCV for a basket of symbols via yfinance.
    Returns {symbol: DataFrame[Open, High, Low, Close, Volume]}, dropping
    any symbol that returns no data (delisted ticker, bad date range,
    typo) rather than silently feeding the generator an empty frame.
    """
    import yfinance as yf

    frames = {}
    for symbol in symbols:
        df = yf.download(symbol, start=start, end=end, interval=interval,
                          multi_level_index=False, progress=False)
        if df is None or df.empty:
            print(f"  ⚠ No data returned for {symbol} — skipping from basket.")
            continue
        df = df[(df["Open"] >= 0) & (df["High"] >= 0) &
                 (df["Low"] >= 0) & (df["Close"] >= 0)].copy()
        frames[symbol] = df[["Open", "High", "Low", "Close", "Volume"]]

    if not frames:
        raise ValueError(
            f"fetch_basket got no usable data for any of {symbols} "
            f"in range {start}..{end} — check symbols and dates."
        )
    return frames
