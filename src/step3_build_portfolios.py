"""
STEP 3 - Mix the investments into portfolios and test them on history ("backtesting").

Question: does mixing investments give a smoother ride than putting everything in
one place, and how much return do you give up for that?

The portfolios we test (weights add up to 100%):
    All US stocks      100% US stocks
    60/40              60% US stocks, 40% bonds  - the classic "balanced" portfolio
    Global 60/40       40% US stocks, 20% international stocks, 40% bonds
    Equal weight       20% in each of the 5 investments
    Defensive          30% US stocks, 50% bonds, 20% gold
    All cash           100% T-bills

Every month the portfolio is reset to its target weights ("rebalancing").
Returns are before taxes and trading costs, but after the ETFs' own small fees.

Outputs:
    results/portfolio_summary.csv, results/portfolio_crashes.csv,
    results/portfolio_calendar_years.csv
    images/portfolios_growth.png, images/portfolios_risk_return.png

Run:  python src/step3_build_portfolios.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import helpers as h

PORTFOLIOS = {
    "All US stocks": {"SPY": 1.0},
    "60/40": {"SPY": 0.6, "AGG": 0.4},
    "Global 60/40": {"SPY": 0.4, "EFA": 0.2, "AGG": 0.4},
    "Equal weight": {"SPY": 0.2, "EFA": 0.2, "AGG": 0.2, "GLD": 0.2, "VNQ": 0.2},
    "Defensive": {"SPY": 0.3, "AGG": 0.5, "GLD": 0.2},
    "All cash": {h.CASH: 1.0},
}


def chart_growth(results):
    fig, ax = plt.subplots(figsize=(10, 6))
    for name, r in results.items():
        value = h.growth(r)
        ax.plot(value.index.to_timestamp(), value, label=name)
    ax.set_title("What $10,000 grew to in each portfolio (Jan 2005 - Sep 2026)")
    ax.set_ylabel("Value ($)")
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(h.IMAGES / "portfolios_growth.png", dpi=120)
    plt.close(fig)


def chart_risk_return(table):
    fig, ax = plt.subplots(figsize=(8, 6))
    x, y = table["volatility"] * 100, table["yearly_return"] * 100
    ax.scatter(x, y, s=80, color="#2a6f97")
    for name in table.index:
        ax.annotate(name, (x[name], y[name]), xytext=(6, 4), textcoords="offset points")
    ax.set_title("Portfolios: return vs risk (higher and further left is better)")
    ax.set_xlabel("Risk: volatility per year (%)")
    ax.set_ylabel("Return per year (%)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(h.IMAGES / "portfolios_risk_return.png", dpi=120)
    plt.close(fig)


def main():
    h.RESULTS.mkdir(exist_ok=True)
    h.IMAGES.mkdir(exist_ok=True)
    returns = h.load_returns()
    cash = returns[h.CASH]

    results = {name: h.portfolio_returns(returns, w) for name, w in PORTFOLIOS.items()}

    table = pd.DataFrame({name: h.summary(r, cash) for name, r in results.items()}).T
    table.round(4).to_csv(h.RESULTS / "portfolio_summary.csv")
    pretty = h.as_percent(table, ["yearly_return", "volatility", "max_drawdown",
                                  "best_year", "worst_year"])
    pretty["sharpe_ratio"] = table["sharpe_ratio"].round(2)
    pretty["value_of_10000"] = table["value_of_10000"].map("${:,.0f}".format)
    print(pretty.to_string(), "\n")

    crashes = pd.DataFrame({crash: {name: h.crash_return(r, s, e) for name, r in results.items()}
                            for crash, (s, e) in h.CRASHES.items()})
    crashes.round(4).to_csv(h.RESULTS / "portfolio_crashes.csv")
    print("Return during each crash:\n", h.as_percent(crashes, crashes.columns).to_string(), "\n")

    years = pd.DataFrame({name: h.calendar_years(r) for name, r in results.items()})
    years.round(4).to_csv(h.RESULTS / "portfolio_calendar_years.csv")

    chart_growth(results)
    chart_risk_return(table)


if __name__ == "__main__":
    main()
