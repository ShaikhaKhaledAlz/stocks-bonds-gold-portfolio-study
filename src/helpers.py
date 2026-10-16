"""
Shared helpers used by every step: loading the data and measuring performance.

If you are new to this project, read this file first. Every number in the
README is calculated by one of the small functions below.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]      # the project folder
DATA = ROOT / "data"
RESULTS = ROOT / "results"
IMAGES = ROOT / "images"

# The 5 investments (ETFs) and what each one represents.
# An ETF is a fund you can buy like a share. Each one holds hundreds of investments.
ASSETS = {
    "SPY": "US stocks",               # S&P 500: the 500 biggest US companies
    "EFA": "International stocks",    # big companies in Europe, Japan, Australia...
    "AGG": "Bonds",                   # US government and company bonds
    "GLD": "Gold",                    # physical gold
    "VNQ": "Real estate",             # REITs: companies that own buildings and collect rent
}
CASH = "Cash"                         # 3-month US Treasury bills (almost no risk)

FIRST_MONTH = "2005-01"   # first month with prices for all 5 ETFs
LAST_MONTH = "2026-09"    # last FULL month in the data (October 2026 was not finished)

# Three market crashes, used to see how each investment held up
CRASHES = {
    "2008 financial crisis": ("2007-11", "2009-02"),
    "2020 COVID crash": ("2020-02", "2020-03"),
    "2022 interest-rate shock": ("2022-01", "2022-09"),
}


# ---------------------------------------------------------------- data
def load_returns():
    """
    Monthly returns for the 5 ETFs and cash, one row per month.
    A return of 0.02 means the investment went up 2% that month.

    The ETF prices are "adjusted": dividends and interest are counted as if they were
    reinvested, so the returns are TOTAL returns, after the ETF's small yearly fee.
    """
    prices = pd.read_csv(DATA / "prices_monthly.csv", index_col="month")
    returns = prices.pct_change()                 # (this month / last month) - 1

    tbill = pd.read_csv(DATA / "tbill_3month.csv")
    tbill["month"] = tbill["observation_date"].str[:7]
    # The T-bill rate is a yearly % (e.g. 4.0). One month of interest = 4.0 / 100 / 12.
    returns[CASH] = tbill.set_index("month")["TB3MS"] / 100 / 12

    returns = returns.loc[FIRST_MONTH:LAST_MONTH]
    returns.index = pd.PeriodIndex(returns.index, freq="M")
    return returns


def portfolio_returns(returns, weights):
    """
    Monthly returns of a portfolio, e.g. weights = {"SPY": 0.6, "AGG": 0.4}.
    We rebalance every month: at the start of each month the money is split again
    in the chosen proportions, so the return is just the weighted average.
    """
    total = sum(weights.values())
    assert abs(total - 1) < 1e-9, f"weights must add up to 1 (100%), they add up to {total}"
    return sum(returns[asset] * weight for asset, weight in weights.items())


# ---------------------------------------------------------------- measures
def growth(r, start=10_000):
    """Value of `start` dollars invested at the beginning, month by month."""
    return start * (1 + r).cumprod()


def yearly_return(r):
    """Average yearly growth rate (CAGR). Turns e.g. 21.75 years of growth into one % per year."""
    years = len(r) / 12
    return (1 + r).prod() ** (1 / years) - 1


def volatility(r):
    """How much returns jump around, per year (standard deviation x square root of 12)."""
    return r.std() * np.sqrt(12)


def sharpe_ratio(r, cash):
    """Extra return above cash, per unit of risk. Higher is better."""
    extra = r - cash
    return extra.mean() * 12 / volatility(r)


def max_drawdown(r):
    """The biggest fall from a peak to a bottom, e.g. -0.55 = lost 55% at the worst point."""
    value = growth(r)
    peak = value.cummax()
    return (value / peak - 1).min()


def calendar_years(r):
    """Return for each full calendar year."""
    by_year = (1 + r).groupby(r.index.year).prod() - 1
    full_years = r.groupby(r.index.year).size() == 12
    return by_year[full_years]


def crash_return(r, start, end):
    """Total return from the start of month `start` to the end of month `end`."""
    return (1 + r.loc[start:end]).prod() - 1


def summary(r, cash):
    """All the key numbers for one investment or portfolio."""
    years = calendar_years(r)
    return {
        "yearly_return": yearly_return(r),
        "volatility": volatility(r),
        "sharpe_ratio": sharpe_ratio(r, cash),
        "max_drawdown": max_drawdown(r),
        "best_year": years.max(),
        "worst_year": years.min(),
        "value_of_10000": growth(r).iloc[-1],
    }


def as_percent(table, columns):
    """Make a table easier to read: 0.0712 -> '7.1%'."""
    out = table.copy()
    for c in columns:
        out[c] = (out[c] * 100).round(1).astype(str) + "%"
    return out
