# E-commerce sales analysis

**2,000 synthetic orders, 573 customers, January 2024–June 2025.** Python, SQL, Excel and Tableau explain revenue, margins, discounts and customer behavior. The notebook now includes RFM targeting, category price-response models, promo-week analysis, a forecast holdout, cohorts, a finite-horizon CLV proxy and a powered A/B test design.

**Data provenance:** the original order dataset is synthetic, with seasonal/category patterns built in. Results demonstrate analytical methods, not evidence about a real retailer. Additional returns and checkout sessions are separately simulated and explicitly labeled; they never change original financial totals.

[Tableau Public dashboard](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/Ecommerce_Sales_Executive_Overview/E-commerceSales-ExecutiveOverview) · [Packaged Tableau workbook](tableau/Ecommerce_Sales_Executive_Overview.twbx) · [Excel workbook](excel/Ecommerce_Sales_Excel_Report.xlsx) · [Detailed findings](findings.md)

## Headline results

| Metric | Value |
|---|---:|
| Orders / customers | 2,000 / 573 |
| Revenue | ₹3,59,28,968.57 |
| Recorded profit / blended margin | ₹51,82,911.58 / 14.43% |
| Profit on 195 orders discounted above 20% | −₹2,48,884.50 |
| Profit on those same orders repriced at 15% | ₹3,26,898.45 |
| Fixed-volume profit difference | **+₹5,75,782.95** |
| Revenue-only top 57 customers' revenue share | 41.18% |
| RFM-ranked top 57 customers' revenue share | 26.79% |
| H1 2025 revenue versus H1 2024 | −18.41% |

The cap scenario holds quantities and implied costs constant; it is **not realized profit uplift**. It covers the requested 195 orders above 20%, not every order above 15%. Revenue-only and RFM rankings define different audiences.

![Monthly revenue and profit](visuals/01_monthly_trend.png)

## Analysis coverage

| Requested item | Implementation |
|---|---|
| RFM segmentation and top-10% targeting | Notebook §5; recency/frequency/monetary tiers, 57-customer audience and offer actions |
| Category price elasticity | §6; weekly normalized-price proxy regression, HAC confidence intervals, +10pp discount response |
| Promo cannibalization | §7; sale-week proxies, full-price units, lead/lag effects and isolated events |
| A/B test for 15% cap | §13; persistent customer randomization, control, profit/customer metric, MDE and calculated sample size |
| Native PivotTable and slicers | Excel `Pivot_Category`; native category/region pivot and both slicers |
| Synthetic-data label | Preserved throughout; no real-data claim |
| Q11 like-for-like H1 comparison | **Already existed** in §4.8; stale README/SQL comments corrected |
| Returns/ratings/cancellations/delivery | None in source; synthetic returns companion added in §8 |
| Checkout funnel | §8; separately simulated browse → cart → checkout → purchase sessions |
| Forecasting with holdout | §9; train Jan–Dec 2024, test Jan–Jun 2025, three models and Jul–Sep forecast |
| Cohort retention and CLV | §10; monthly retention with future ages blank and 12-month value proxy |
| Discount versus margin significance | §11; product/region/month controls, customer-clustered 95% interval |
| Profit gain from cap | §12, SQL Q10b and findings; per-order cent-rounded repricing |
| Published margin benchmarks | Findings §12; dated NYU Stern retail benchmarks and comparability caveats |
| Data dictionary | All 13 original columns below |
| License and CI | MIT `LICENSE`; GitHub Action runs SQL verification and notebook/artifact checks |

Price response and cannibalization are **observational**, not causal. Returns/funnel rates are simulations, not observed KPIs. The forecast beats neither reality nor uncertainty: the best holdout baseline still has 32.79% WAPE.

## Data dictionary

The committed `ecommerce_sales.csv` remains **2,000 rows × 13 columns**, one row per distinct order ID. Currency is INR; monetary fields are recorded to two decimal places.

| Column | Type | Meaning / interpretation |
|---|---|---|
| `order_id` | string | Unique synthetic order identifier; one row per order |
| `order_date` | date | Order date, 2024-01-01 through 2025-06-30 |
| `customer_id` | string | Synthetic customer identifier; repeat orders share the ID |
| `region` | string | North, South, East or West |
| `category` | string | Beauty, Electronics, Fashion, Home & Kitchen or Sports |
| `sub_category` | string | Product subgroup within the category |
| `product` | string | Synthetic product name; not a real catalog claim |
| `quantity` | integer | Units on the order; positive, observed range 1–5 |
| `unit_price` | decimal | List price per unit before discount, INR |
| `discount` | decimal | Discount fraction, not percentage points; 0.15 means 15%; observed 0–0.40 |
| `sales` | decimal | Recorded order revenue after discount; approximately quantity × unit_price × (1 − discount), allowing cent rounding |
| `profit` | decimal | Recorded synthetic order profit, INR; implied cost = sales − profit; not audited net income |
| `payment_method` | string | UPI, Credit Card, Debit Card, Net Banking or Cash on Delivery |

### Simulated companions and generated outputs

The notebook regenerates 21 CSVs under `analysis_data/`:

- `synthetic_order_outcomes.csv`: one row per original order; `order_id`, `category`, `returned_synthetic` (Boolean), `is_synthetic` (always true). Return probabilities are explicitly assumed by category; original profit is not adjusted.
- `synthetic_funnel_sessions.csv`: 10,000 independent demo sessions; `session_id`, nested Boolean `browsed`, `added_to_cart`, `checkout_started`, `purchased`, and `is_synthetic` (always true). Simulated purchases are not historical order records.
- `synthetic_funnel_summary.csv`: stage counts, previous-stage/browse conversion and dropoff.
- RFM audience/customer tables, category/week demand and elasticity, promo weekly/effect/event tables, forecast holdout/metrics/future tables, cohort retention/sizes, CLV curve/summary, discount-margin regression, cap order/summary tables and A/B sizing assumptions.

Simulation seed: **20251027**. Observed zero-purchase cohort months are zero; unobservable future months are blank. Category price-response fits omit zero-order category/weeks because offered discounts are unknown. These generated tables are committed and checked for numeric drift when the notebook is rerun.

## Excel reporting workbook

Open [Ecommerce_Sales_Excel_Report.xlsx](excel/Ecommerce_Sales_Excel_Report.xlsx) in desktop Microsoft Excel. Start with `KPI_Dashboard`; use `Pivot_Category` for native interactive filtering.

| Sheet | Contents |
|---|---|
| `KPI_Dashboard` | Formula-based KPI scorecard and monthly sales summary |
| `Monthly_Trend` | Monthly orders, sales, profit and margin |
| `Category_Region` | Category and regional summaries |
| `Discount_Payment` | Discount-bucket and payment summaries |
| `Pivot_Category` | **Native PivotTable**: category rows, region columns, SUM sales, SUM profit, COUNT orders; native Region and Category slicers |
| `Quality_Checks` | Eight pass/fail data checks plus loss-making-order information |
| `Clean_Data` | Original orders plus month, discount bucket, margin and loss flags; source table `Orders_Clean` |
| `Raw_Data` | Original 13-column source |

The two slicers filter the native pivot only, not the separate formula-based dashboard. Clear both to restore all 2,000 orders. All four regions, five categories and 20 intersections were tested in Excel after saving; all eight quality checks pass. Other sheets' formulas/data are preserved.

To rebuild and validate the native pivot on **Windows with Excel installed**:

```powershell
python excel/build_native_pivot.py
```

The workbook is saved through Excel automation, not openpyxl, to preserve native slicers. Linux CI does not execute Excel COM; it verifies SQL and the notebook.

## Reproduce and verify

Use Python 3.11 or newer; the CI environment uses 3.11. From the repository root:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python sql/verify_sql.py
python verify_analysis.py
jupyter notebook Ecommerce_Sales_Analysis.ipynb
```

`verify_sql.py` runs **133 assertions** across 14 MySQL statements, transpiled with sqlglot and executed in DuckDB. It checks baseline expected values, independent pandas comparisons and cent-rounded cap arithmetic; it does not test a running MySQL server. `verify_analysis.py` executes every notebook code cell, regenerates the executed notebook/21 artifact tables, checks source immutability, and verifies RFM, simulation, cohort censoring, CLV, holdout metrics, inference and cap results. Existing output tables must reproduce without numeric drift.

The GitHub Action in `.github/workflows/verify.yml` runs both commands on push and pull requests with read-only repository permissions.

### MySQL 8.0

```bash
mysql -u root -p < sql/schema.sql
mysql --local-infile=1 -u root -p < sql/load_data.sql
mysql -u root -p ecommerce_sales < sql/analysis_queries.sql
```

| Query | Output |
|---|---|
| Q1 | Revenue, profit, margin, orders, customers, AOV and date range |
| Q2 | Monthly trend |
| Q3 | Category revenue/profit shares and blended margin |
| Q4 | Region revenue, orders, AOV and margin |
| Q5 | Discount buckets, mean order margin and losses |
| Q6 | Top 10 products |
| Q7 / Q7b | Repeat rate / revenue-only top-decile concentration |
| Q8 | Payment-method mix |
| Q9 | Category × region mean order margins (not blended margins) |
| Q10 | Original loss on orders discounted above 20% |
| Q10b | Same 195 orders repriced at 15%, fixed quantities/costs |
| Q11 | Like-for-like H1 2024 versus H1 2025, notebook §4.8 |
| Q12 | Deep-discount damage by category |

## Files

- `Ecommerce_Sales_Analysis.ipynb`: executed case study, 49 cells.
- `ecommerce_sales.csv`: unchanged synthetic source.
- `analysis_data/`: 21 reproducible analysis/demo tables.
- `findings.md`: results, experiment design and benchmark sources.
- `sql/`: schema, loading, analysis queries and verifier.
- `excel/`: reporting workbook and native-pivot rebuild/validation script.
- `tableau/`: original packaged executive dashboard; not extended with the new analyses.
- `visuals/`: original seven plots regenerated by the notebook plus the cohort heatmap.
- `verify_analysis.py`, `requirements.txt`, `.github/workflows/verify.yml`, `LICENSE`.

## License

[MIT License](LICENSE). The source transactions and additional demo events are synthetic; the published industry benchmarks are external references, not project data.
