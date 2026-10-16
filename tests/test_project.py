"""
Automatic checks. GitHub runs them after every change (.github/workflows/check.yml).
Run them yourself with:  pytest
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import helpers as h  # noqa: E402
import step2_compare_assets  # noqa: E402
import step3_build_portfolios  # noqa: E402
import step4_efficient_frontier  # noqa: E402


def test_data_has_no_gaps():
    r = h.load_returns()
    assert r.isna().sum().sum() == 0
    assert len(r) == 261                       # Jan 2005 to Sep 2026


def test_measures_on_a_simple_example():
    # 1% every month for 12 months -> 12.68% in a year, no volatility, no drawdown
    r = pd.Series([0.01] * 12, index=pd.period_range("2020-01", periods=12, freq="M"))
    assert abs(h.yearly_return(r) - (1.01 ** 12 - 1)) < 1e-12
    assert h.max_drawdown(r) == 0
    # up 50% then down 50% -> fell 50% from the peak
    r2 = pd.Series([0.5, -0.5], index=pd.period_range("2020-01", periods=2, freq="M"))
    assert abs(h.max_drawdown(r2) + 0.5) < 1e-12


def test_portfolio_is_weighted_average():
    r = h.load_returns()
    p = h.portfolio_returns(r, {"SPY": 0.6, "AGG": 0.4})
    assert np.allclose(p, 0.6 * r["SPY"] + 0.4 * r["AGG"])


def test_all_steps_run():
    step2_compare_assets.main()
    step3_build_portfolios.main()
    step4_efficient_frontier.main()
    for f in ["asset_summary.csv", "portfolio_summary.csv", "hindsight_test.csv"]:
        assert (h.RESULTS / f).exists()
