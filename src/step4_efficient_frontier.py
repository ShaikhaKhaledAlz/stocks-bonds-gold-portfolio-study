"""
STEP 4 - The efficient frontier, and why "the best portfolio" is only best in hindsight.

Part A - Efficient frontier
    We try 20,000 random mixes of the 5 investments (no borrowing, no short selling,
    weights add up to 100%). For each mix we measure return and risk. The upper-left
    edge of the cloud is the "efficient frontier": for each level of risk, the highest
    return that was possible. We highlight:
        - the mix with the highest Sharpe ratio (best return per unit of risk)
        - the mix with the lowest risk

Part B - Hindsight test
    Finding the best mix AFTER seeing the data is easy. The real question is whether
    it keeps working. So we find the best-Sharpe mix using only 2005-2015, then check
    how it did in 2016-2026, compared with a simple 60/40 portfolio.

Outputs:
    results/frontier_best_mixes.csv, results/hindsight_test.csv
    images/efficient_frontier.png

Run:  python src/step4_efficient_frontier.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import helpers as h

N_MIXES = 20_000
SEED = 42                      # fixed seed = the same "random" mixes every run
TICKERS = list(h.ASSETS)       # the 5 investments (cash is left out)
SPLIT = "2015-12"              # Part B: learn up to here, test after


def random_mixes(n, seed=SEED):
    """
    n random sets of weights for the 5 investments. Each row adds up to 1.
    Half are "spread out" mixes, half are "concentrated" mixes (mostly 1-2 investments),
    plus the 5 single investments, so the edges of the cloud are covered too.
    """
    rng = np.random.default_rng(seed)
    k = len(TICKERS)
    spread = rng.dirichlet(np.ones(k), size=n // 2)
    concentrated = rng.dirichlet(np.full(k, 0.15), size=n - n // 2 - k)
    singles = np.eye(k)
    return np.vstack([spread, concentrated, singles])


def score_mixes(returns, weights):
    """Return per year, risk per year and Sharpe ratio for every mix (fast, all at once)."""
    monthly = returns[TICKERS].to_numpy() @ weights.T          # months x mixes
    years = len(returns) / 12
    yearly_ret = np.prod(1 + monthly, axis=0) ** (1 / years) - 1
    vol = monthly.std(axis=0, ddof=1) * np.sqrt(12)
    extra = monthly - returns[h.CASH].to_numpy()[:, None]
    sharpe = extra.mean(axis=0) * 12 / vol
    return pd.DataFrame({"yearly_return": yearly_ret, "volatility": vol, "sharpe_ratio": sharpe})


def describe(weights_row):
    return {t: round(float(w), 3) for t, w in zip(TICKERS, weights_row)}


def nice(weights_dict):
    """{'SPY': 0.42, ...} -> '42% US stocks, ...' (only weights of 1% or more)."""
    parts = [f"{w:.0%} {h.ASSETS[t]}" for t, w in sorted(weights_dict.items(), key=lambda x: -x[1])
             if w >= 0.01]
    return ", ".join(parts)


def main():
    h.RESULTS.mkdir(exist_ok=True)
    h.IMAGES.mkdir(exist_ok=True)
    returns = h.load_returns()
    weights = random_mixes(N_MIXES)

    # ---------------- Part A: whole period
    scores = score_mixes(returns, weights)
    best = scores["sharpe_ratio"].idxmax()
    safest = scores["volatility"].idxmin()
    best_mixes = pd.DataFrame({
        "Highest Sharpe ratio": {**scores.loc[best].to_dict(), **describe(weights[best])},
        "Lowest risk": {**scores.loc[safest].to_dict(), **describe(weights[safest])},
    }).T
    best_mixes.round(4).to_csv(h.RESULTS / "frontier_best_mixes.csv")
    print("Part A - best mixes, Jan 2005 to Sep 2026:")
    for label, row in best_mixes.iterrows():
        print(f"  {label}: {nice(row[TICKERS].to_dict())}")
        print(f"    return {row.yearly_return:.1%}/yr, risk {row.volatility:.1%}, "
              f"Sharpe {row.sharpe_ratio:.2f}")

    # chart: the cloud of random mixes, the single investments and the two best mixes
    cash = returns[h.CASH]
    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(scores["volatility"] * 100, scores["yearly_return"] * 100,
                    c=scores["sharpe_ratio"], cmap="viridis", s=3, alpha=0.5)
    fig.colorbar(sc, ax=ax, label="Sharpe ratio")
    for t in TICKERS:
        r = returns[t]
        ax.scatter(h.volatility(r) * 100, h.yearly_return(r) * 100, color="black", s=40)
        ax.annotate(h.ASSETS[t], (h.volatility(r) * 100, h.yearly_return(r) * 100),
                    xytext=(5, 3), textcoords="offset points", fontsize=8)
    for label, row, color in [("Highest Sharpe", scores.loc[best], "red"),
                              ("Lowest risk", scores.loc[safest], "orange")]:
        ax.scatter(row.volatility * 100, row.yearly_return * 100, marker="*", s=300,
                   color=color, edgecolor="black", label=label, zorder=3)
    sixty = h.portfolio_returns(returns, {"SPY": 0.6, "AGG": 0.4})
    ax.scatter(h.volatility(sixty) * 100, h.yearly_return(sixty) * 100, marker="D", s=80,
               color="white", edgecolor="black", label="60/40", zorder=3)
    ax.set_title(f"{N_MIXES:,} random mixes of the 5 investments, Jan 2005 - Sep 2026")
    ax.set_xlim(right=scores["volatility"].max() * 100 + 3)   # room for the labels
    ax.set_xlabel("Risk: volatility per year (%)")
    ax.set_ylabel("Return per year (%)")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(h.IMAGES / "efficient_frontier.png", dpi=120)
    plt.close(fig)

    # ---------------- Part B: hindsight test
    learn, test = returns.loc[:SPLIT], returns.loc[pd.Period(SPLIT, "M") + 1:]
    learned = score_mixes(learn, weights)["sharpe_ratio"].idxmax()
    learned_weights = describe(weights[learned])
    rows = {}
    for label, w in [("Best mix chosen in 2005-2015", learned_weights),
                     ("60/40", {"SPY": 0.6, "AGG": 0.4})]:
        w = {t: v for t, v in w.items() if v > 0}
        w = {t: v / sum(w.values()) for t, v in w.items()}     # make rounding add up to 100%
        for period, data in [("2005-2015 (learning)", learn), ("2016-2026 (test)", test)]:
            r = h.portfolio_returns(data, w)
            rows[(label, period)] = {"yearly_return": h.yearly_return(r),
                                     "volatility": h.volatility(r),
                                     "sharpe_ratio": h.sharpe_ratio(r, data[h.CASH])}
    hindsight = pd.DataFrame(rows).T
    hindsight.index.names = ["portfolio", "period"]
    hindsight.round(4).to_csv(h.RESULTS / "hindsight_test.csv")
    print(f"\nPart B - best mix found using 2005-2015 only: {nice(learned_weights)}")
    print(h.as_percent(hindsight, ["yearly_return", "volatility"]).round(2).to_string())


if __name__ == "__main__":
    main()
