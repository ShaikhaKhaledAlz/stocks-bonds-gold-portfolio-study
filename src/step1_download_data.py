"""
STEP 1 - Download the data (optional: the data is already in the data/ folder).

Run this only if you want to update the data to the latest month.

Sources (both free):
    Yahoo Finance  monthly prices of 5 ETFs, adjusted for dividends and splits
                   (so returns include the dividends / interest each fund paid out)
    FRED           3-month US Treasury bill rate, series TB3MS (Federal Reserve Bank of St. Louis)

Saves:
    data/prices_monthly.csv   one row per month, one column per ETF
    data/tbill_3month.csv     one row per month, the T-bill rate in % per year

After updating, change LAST_MONTH in src/helpers.py to the last FULL month.

Run:  python src/step1_download_data.py
      python src/step1_download_data.py --out some/other/folder    (save somewhere else)
"""
import argparse
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = ["SPY", "EFA", "AGG", "GLD", "VNQ"]
START = "2004-12-01"     # one month before the study starts, to compute January 2005's return
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TB3MS&cosd=2004-12-01"


def download_prices():
    # auto_adjust=True: prices are adjusted for dividends and splits
    raw = yf.download(TICKERS, start=START, interval="1mo", auto_adjust=True, progress=False)
    prices = raw["Close"][TICKERS]
    prices.index = prices.index.strftime("%Y-%m")
    prices.index.name = "month"
    return prices.dropna().round(4)


def download_tbill():
    return pd.read_csv(FRED_URL)


def main():
    parser = argparse.ArgumentParser(description="Download monthly prices and T-bill rates.")
    parser.add_argument("--out", default=Path(__file__).resolve().parents[1] / "data",
                        help="folder to save the files in (default: data/)")
    out = Path(parser.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    prices = download_prices()
    prices.to_csv(out / "prices_monthly.csv")
    print(f"Prices: {len(prices)} months, {prices.index[0]} to {prices.index[-1]}")

    tbill = download_tbill()
    tbill.to_csv(out / "tbill_3month.csv", index=False)
    print(f"T-bill: {len(tbill)} months, last value {tbill.iloc[-1, 1]}%")
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
