"""
STEP 2 - Compare the investments one by one.

Question: how did US stocks, international stocks, bonds, gold, real estate and cash
each perform from January 2005 to September 2026, and how much risk did they carry?

Outputs:
    results/asset_summary.csv     return, risk, Sharpe ratio, worst fall, best/worst year
    results/correlations.csv      how much the investments move together
    results/crashes.csv           how each investment did in 3 market crashes
    images/growth_of_10000.png    what $10,000 grew to
    images/correlations.png       correlation heatmap
    images/drawdowns.png          how far each one fell below its previous peak

Run:  python src/step2_compare_assets.py
"""
import matplotlib

matplotlib.use("Agg")   # save charts to files without opening a window
import matplotlib.pyplot as plt

import helpers as h

COLORS = {"SPY": "#1f77b4", "EFA": "#17becf", "AGG": "#2ca02c", "GLD": "#d4a017",
          "VNQ": "#9467bd", "Cash": "#7f7f7f"}


def name(ticker):
    """'SPY' -> 'US stocks (SPY)'"""
    return f"{h.ASSETS[ticker]} ({ticker})" if ticker in h.ASSETS else ticker


def chart_growth(returns):
    fig, ax = plt.subplots(figsize=(10, 6))
    for t in returns.columns:
        value = h.growth(returns[t])
        ax.plot(value.index.to_timestamp(), value, label=name(t), color=COLORS[t])
    ax.set_title("What $10,000 invested in January 2005 grew to (dividends reinvested)")
    ax.set_ylabel("Value ($)")
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(h.IMAGES / "growth_of_10000.png", dpi=120)
    plt.close(fig)


def chart_correlations(corr):
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [h.ASSETS.get(t, t) for t in corr.columns]
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(corr)):
        for j in range(len(corr)):
            v = corr.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9,
                    color="white" if abs(v) > 0.6 else "black")   # readable on dark cells
    ax.set_title("Correlation of monthly returns\n(1 = move together, 0 = unrelated, -1 = opposite)")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(h.IMAGES / "correlations.png", dpi=120)
    plt.close(fig)


def chart_drawdowns(returns):
    fig, ax = plt.subplots(figsize=(10, 5))
    for t in ["SPY", "EFA", "VNQ", "GLD", "AGG"]:
        value = h.growth(returns[t])
        below_peak = (value / value.cummax() - 1) * 100
        ax.plot(below_peak.index.to_timestamp(), below_peak, label=name(t), color=COLORS[t])
    ax.set_title("How far below its previous peak each investment was (%)")
    ax.set_ylabel("% below peak")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(h.IMAGES / "drawdowns.png", dpi=120)
    plt.close(fig)


def main():
    h.RESULTS.mkdir(exist_ok=True)
    h.IMAGES.mkdir(exist_ok=True)
    returns = h.load_returns()
    cash = returns[h.CASH]
    first, last = returns.index[0], returns.index[-1]
    print(f"Data: {first} to {last} ({len(returns)} months)\n")

    # 1. key numbers for each investment
    table = h.pd.DataFrame({name(t): h.summary(returns[t], cash) for t in returns.columns}).T
    table = table.sort_values("sharpe_ratio", ascending=False)
    table.round(4).to_csv(h.RESULTS / "asset_summary.csv")
    pretty = h.as_percent(table, ["yearly_return", "volatility", "max_drawdown",
                                  "best_year", "worst_year"])
    pretty["sharpe_ratio"] = table["sharpe_ratio"].round(2)
    pretty["value_of_10000"] = table["value_of_10000"].map("${:,.0f}".format)
    print(pretty.to_string(), "\n")

    # 2. correlations (cash is left out: its return barely moves, so it isn't informative)
    corr = returns[list(h.ASSETS)].corr()
    corr.round(3).to_csv(h.RESULTS / "correlations.csv")
    print("Correlations:\n", corr.round(2).to_string(), "\n")

    # 3. crashes
    crashes = h.pd.DataFrame({crash: {name(t): h.crash_return(returns[t], s, e)
                                      for t in returns.columns}
                              for crash, (s, e) in h.CRASHES.items()})
    crashes.round(4).to_csv(h.RESULTS / "crashes.csv")
    print("Return during each crash:\n", h.as_percent(crashes, crashes.columns).to_string())

    chart_growth(returns)
    chart_correlations(corr)
    chart_drawdowns(returns)


if __name__ == "__main__":
    main()
