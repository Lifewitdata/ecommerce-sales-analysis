import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
import numpy as np
import pandas as pd
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "Ecommerce_Sales_Analysis.ipynb"
ARTIFACTS = ROOT / "analysis_data"


def main():
    source_hash = hashlib.sha256((ROOT / "ecommerce_sales.csv").read_bytes()).hexdigest()
    existing = {path.name: pd.read_csv(path) for path in ARTIFACTS.glob("*.csv")}
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    with TemporaryDirectory() as directory:
        kernel_dir = Path(directory) / "ecommerce-verification"
        kernel_dir.mkdir()
        (kernel_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Ecommerce verification", "language": "python"}), encoding="utf-8")
        manager = KernelManager(kernel_name="ecommerce-verification",
                                kernel_spec_manager=KernelSpecManager(kernel_dirs=[directory]))
        try:
            NotebookClient(notebook, km=manager, timeout=180, record_timing=False,
                           resources={"metadata": {"path": str(ROOT)}}).execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    nbformat.write(notebook, NOTEBOOK)
    assert hashlib.sha256((ROOT / "ecommerce_sales.csv").read_bytes()).hexdigest() == source_hash
    for name, previous in existing.items():
        pd.testing.assert_frame_equal(previous, pd.read_csv(ARTIFACTS / name),
                                      check_exact=False, atol=1e-8, rtol=1e-10)

    source = pd.read_csv(ROOT / "ecommerce_sales.csv", parse_dates=["order_date"])
    rfm = pd.read_csv(ARTIFACTS / "rfm_customers.csv")
    target = pd.read_csv(ARTIFACTS / "rfm_target_top10pct.csv")
    assert len(rfm) == source.customer_id.nunique() == 573
    assert len(target) == rfm.target_top_10pct.sum() == 57
    assert target.customer_id.tolist() == rfm.head(57).customer_id.tolist()
    assert rfm[["R", "F", "M"]].isin(range(1, 6)).all().all()
    for row in rfm.itertuples():
        orders = source[source.customer_id == row.customer_id]
        assert row.recency_days == (source.order_date.max() + pd.Timedelta(days=1) - orders.order_date.max()).days
        assert row.frequency == orders.order_id.nunique()
        assert np.isclose(row.monetary, orders.sales.sum())

    outcomes = pd.read_csv(ARTIFACTS / "synthetic_order_outcomes.csv")
    sessions = pd.read_csv(ARTIFACTS / "synthetic_funnel_sessions.csv")
    funnel = pd.read_csv(ARTIFACTS / "synthetic_funnel_summary.csv", index_col="stage")
    assert outcomes.order_id.is_unique and set(outcomes.order_id) == set(source.order_id)
    assert outcomes.is_synthetic.all() and sessions.is_synthetic.all()
    assert len(sessions) == 10000 and sessions.session_id.is_unique
    assert (~sessions.purchased | sessions.checkout_started).all()
    assert (~sessions.checkout_started | sessions.added_to_cart).all()
    assert (~sessions.added_to_cart | sessions.browsed).all()
    for stage in funnel.index:
        assert funnel.loc[stage, "sessions"] == sessions[stage].sum()

    retention = pd.read_csv(ARTIFACTS / "cohort_retention.csv", index_col="cohort")
    sizes = pd.read_csv(ARTIFACTS / "cohort_sizes.csv", index_col="cohort").customers
    purchase_month = source.order_date.dt.to_period("M")
    first_month = source.assign(month=purchase_month).groupby("customer_id").month.min()
    for cohort, row in retention.iterrows():
        cohort_month = pd.Period(cohort, freq="M")
        customers = first_month[first_month == cohort_month].index
        assert sizes.loc[cohort] == len(customers)
        for age, value in row.items():
            month = cohort_month + int(age)
            if month > purchase_month.max():
                assert pd.isna(value)
            else:
                active = source[source.customer_id.isin(customers) & (purchase_month == month)].customer_id.nunique()
                assert np.isclose(value, active / len(customers))
    clv = pd.read_csv(ARTIFACTS / "clv_summary.csv").iloc[0]
    mature = first_month[first_month <= purchase_month.max() - 11]
    age = np.array([month.ordinal - first_month[customer].ordinal
                    for month, customer in zip(purchase_month, source.customer_id)])
    mature_orders = source[source.customer_id.isin(mature.index) & (age < 12)]
    assert clv.mature_customers == len(mature)
    assert np.isclose(clv.revenue_clv_proxy, mature_orders.sales.sum() / len(mature))
    assert np.isclose(clv.gross_profit_clv_proxy, mature_orders.profit.sum() / len(mature))

    holdout = pd.read_csv(ARTIFACTS / "forecast_holdout.csv", index_col="month")
    metrics = pd.read_csv(ARTIFACTS / "forecast_metrics.csv")
    monthly = source.groupby(purchase_month).sales.sum()
    assert list(holdout.index) == list(pd.period_range("2025-01", "2025-06", freq="M").astype(str))
    np.testing.assert_allclose(holdout.actual_revenue, monthly.iloc[12:].values)
    np.testing.assert_allclose(holdout.seasonal_naive, monthly.iloc[:6].values)
    np.testing.assert_allclose(holdout.last_month_naive, monthly.iloc[11])
    for row in metrics.itertuples():
        error = holdout[row.model] - holdout.actual_revenue
        np.testing.assert_allclose([row.mae, row.rmse, row.wape],
            [np.abs(error).mean(), np.sqrt(np.mean(error ** 2)), np.abs(error).sum() / holdout.actual_revenue.sum()])
    future = pd.read_csv(ARTIFACTS / "forecast_future.csv")
    assert list(future.month) == ["2025-07", "2025-08", "2025-09"]
    assert future.forecast_revenue.gt(0).all()
    assert future.model.eq(metrics.sort_values("wape").iloc[0].model).all()

    elasticity = pd.read_csv(ARTIFACTS / "category_elasticity.csv")
    assert set(elasticity.category) == set(source.category)
    assert np.isfinite(elasticity.select_dtypes("number")).all().all()
    assert (elasticity.ci_low <= elasticity.elasticity).all()
    assert (elasticity.elasticity <= elasticity.ci_high).all()
    promo = pd.read_csv(ARTIFACTS / "promo_weekly.csv")
    assert promo.sale.equals((promo.deep_order_share >= .15).astype(int))
    assert pd.to_datetime(promo.week).max() < source.order_date.max().to_period("W-SUN").start_time
    regression = pd.read_csv(ARTIFACTS / "discount_margin_regression.csv").iloc[0]
    assert regression.ci_low <= regression.coefficient <= regression.ci_high
    assert regression.customer_clusters == 573
    cap = pd.read_csv(ARTIFACTS / "discount_cap_summary.csv").iloc[0]
    assert cap.orders == 195
    np.testing.assert_allclose([cap.original_profit, cap.capped_profit, cap.profit_difference],
                               [-248884.50, 326898.45, 575782.95], atol=.005, rtol=0)
    ab = pd.read_csv(ARTIFACTS / "ab_sample_size.csv").iloc[0]
    assert ab.alpha == .05 and ab.power == .8
    assert ab.planned_total == 2 * ab.planned_per_arm
    assert ab.planned_per_arm >= ab.required_per_arm > 573
    print(f"PASS: all notebook code cells executed; {len(list(ARTIFACTS.glob('*.csv')))} artifacts verified")
    print("PASS: source unchanged; RFM, simulation, cohorts, CLV, holdout, inference and cap checks")
    if existing:
        print(f"PASS: {len(existing)} committed artifact tables reproduced without numeric drift")


if __name__ == "__main__":
    main()
