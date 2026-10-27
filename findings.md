# E-commerce sales findings and test plan

All 2,000 orders are **synthetic**. Values below are reproducible demonstrations of analysis methods, not claims about a real retailer. Returns and funnel events are additional simulations and are kept separate from the 13-column financial source.

## 1. Baseline

| Metric | Result |
|---|---:|
| Customers | 573 |
| Revenue | ₹3,59,28,968.57 |
| Recorded profit / margin | ₹51,82,911.58 / 14.43% |
| H1 2025 revenue vs H1 2024 | −18.41% |
| Revenue-only top 57 customer share | 41.18% |

Electronics generates 71.74% of revenue but 44.39% of profit at an 8.93% blended margin. Beauty's blended margin is 45.89%, but that category-level difference does **not** show that shifting a rupee of demand between categories would preserve volume or margin.

## 2. Discount cap scenario: correct profit difference

Q10 identifies the 195 orders discounted above 20%: ₹28,99,323.45 revenue and **−₹2,48,884.50 profit**.

For those same 195 orders only, the notebook and SQL Q10b set the discount to 15%, keep quantity and implied cost (`sales − profit`) fixed, and round each repriced order to cents:

| Scenario | Sales | Profit |
|---|---:|---:|
| Recorded discounts above 20% | ₹28,99,323.45 | −₹2,48,884.50 |
| Same orders at a 15% cap | ₹34,75,106.40 | ₹3,26,898.45 |
| Difference | **+₹5,75,782.95** | **+₹5,75,782.95** |

The profit difference is **₹5,75,782.95**, not ₹2.49 lakh. The latter is only the removal of the current loss, while repricing also creates positive margin. This is fixed-volume accounting, not realized uplift: customer response, competitors, inventory, returns and campaign exposure are not modeled. It excludes discounts of 15–20%, so it is not a simulation of a full blanket cap.

## 3. RFM target

RFM uses a 1 July 2025 snapshot, days since last purchase, distinct order count and recorded revenue. Equal metric values receive equal 1–5 percentile tiers. The top 57 customers are selected by total RFM tier, then monetary value and customer ID.

- RFM audience: **57 customers** (floor of 10%).
- Historical revenue share: **26.79%**.
- Recent customers receive VIP access/no blanket discount; older customers receive capped reminder or win-back tests.

The revenue-only top 57 share remains 41.18%; it is a different ranking. Historical targeting does not prove incremental retention.

## 4. Category price response

Weekly log-unit models use a normalized net-price proxy (`1 − quantity-weighted discount`), time and annual sine/cosine terms, with HAC(4) confidence intervals. A +10 percentage-point discount is associated with:

| Category | Price elasticity estimate (95% CI) | Associated unit-demand change (95% CI) |
|---|---:|---:|
| Beauty | 1.93 (−1.00, 4.86) | −20.12% (−43.19%, 12.32%) |
| Electronics | 2.72 (0.56, 4.87) | −27.15% (−43.33%, −6.35%) |
| Fashion | 1.14 (−1.58, 3.85) | −12.63% (−36.69%, 20.56%) |
| Home & Kitchen | −2.48 (−5.59, 0.62) | +33.34% (−6.88%, 90.94%) |
| Sports | 0.51 (−1.36, 2.39) | −5.84% (−24.37%, 17.24%) |

Most intervals include zero; positive elasticity estimates are economically counterintuitive and signal confounding/product-mix problems rather than a reason to believe discounts reduce demand. Purchase discounts omit non-buyers, offer exposure, inventory and competitors. These are observational associations, **not causal elasticities**.

## 5. Sale-week proxies and cannibalization

With no campaign calendar, a sale-week proxy means at least 15% of recorded orders were discounted above 20%. Controlling for trend and annual terms, full-price units were:

| Term | Coefficient in full-price units (95% CI) | p-value |
|---|---:|---:|
| Sale week | −3.39 (−5.64, −1.14) | 0.003 |
| Week after a sale | +1.59 (−1.57, 4.75) | 0.324 |
| Week before a sale | −0.12 (−2.75, 2.51) | 0.928 |

There is same-week substitution away from full-price units in this synthetic sample. There is **no statistically clear pre-sale waiting or post-sale dip**, so pull-forward cannibalization is not established. Sale classification is derived from purchases rather than scheduled offers and may capture mix or seasonal effects.

## 6. Funnel and returns are simulated

The original 13 columns contain no return, rating, cancellation, delivery or session data. The notebook therefore creates clearly marked companion data with seed 20251027:

- 138 simulated returns among 2,000 orders, based on explicit category probability assumptions. Original profit is not adjusted.
- 10,000 simulated browsing sessions: 3,308 carts, 2,133 checkout starts and 1,512 purchases. Rates are 33.08% browse→cart, 64.48% cart→checkout, and 70.89% checkout→purchase.

These are workflow demonstrations, not observed KPIs or external benchmarks.

## 7. Forecast holdout

Models train on Jan–Dec 2024 and are evaluated once on Jan–Jun 2025:

| Model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| Seasonal naive | ₹5,34,179.77 | ₹6,83,855.08 | **32.79%** |
| Last-month naive | ₹13,12,752.44 | ₹13,22,605.32 | 80.57% |
| Log trend + annual seasonality | ₹42,98,229.23 | ₹43,64,557.23 | 263.82% |

Seasonal naive wins but 32.79% WAPE is weak. Only one training year and six holdout months are available; no calibrated prediction interval is claimed. The Jul–Sep 2025 forecast is provisional, and selecting the model on the same holdout makes its reported score optimistic for future use.

## 8. Cohorts and customer value

Monthly cohort retention uses each customer's first **observed** order. Age zero is 100%; observed inactivity is zero and future/unobservable cohort ages are blank. Purchases before January 2024 are unknown.

Mature cohorts with 12 observable months contain 436 customers. Their finite 12-month averages are:

- Revenue CLV proxy: **₹57,481.95 per original cohort customer**.
- Gross-profit-like CLV proxy: **₹8,438.82**.
- Historical revenue/customer across the full sample: ₹62,703.26 (different exposure windows, not a fair 12-month comparison).

This is not full lifetime value. It excludes acquisition cost, operating expenses, refunds and discounting and assumes earlier cohorts are informative for newer ones.

## 9. Discount–margin significance

Order margin is regressed on discount with product, region and calendar-month fixed effects and customer-clustered standard errors. A +10pp discount is associated with **−11.46 margin percentage points** (95% CI −11.57 to −11.34; p < 0.001).

The relationship is statistically precise because margin's denominator already includes discounted sales and the synthetic generator embeds discount behavior. It is not a causal policy estimate and does not replace the experiment.

## 10. A/B test for the 15% blanket cap

**Population and assignment.** Registered promotion-eligible customers; persistent 1:1 customer-level randomization, stratified by prior spend tier and region. Hold catalog, campaign exposure and shipping constant. Do not analyze only purchasers.

**Control.** Current discount policy. **Treatment.** Blanket offers capped at 15%. This tests the full policy, not only the 195-order scenario.

**Primary metric.** Intention-to-treat realized contribution profit per assigned customer over 28 days, including zero for non-buyers and refund/variable fulfillment costs. Wait 14 additional days for returns. Success requires a positive treatment-minus-control difference with a two-sided 95% CI excluding zero. Report revenue and conversion separately and investigate refund/complaint deterioration before rollout.

**Sample size.** Two-sided α=0.05, 80% power, 10% relative minimum detectable improvement. The synthetic trailing 28-day profit/customer proxy has mean ₹476.30 and SD ₹2,439.31. Normal approximation gives 41,173 customers/arm; after 10% instrumentation allowance: **45,748 per arm, 91,496 total**.

This synthetic variance proxy is unstable and heavy-tailed. Re-estimate variance in a live instrumentation pilot; use a customer bootstrap sensitivity check. The current 573-customer dataset is underpowered. One final read only—no optional stopping.

## 11. Native Excel verification

`Pivot_Category` is now a real Excel PivotTable over `Orders_Clean`, with category rows, region columns, SUM sales, SUM profit and COUNT order ID. Native Region and Category slicers were tested across four regions, five categories and all 20 intersections after save/reopen. Clearing restores ₹3,59,28,968.57 sales, ₹51,82,911.58 profit and 2,000 orders; all eight quality checks pass.

The two slicers filter the pivot, not the formula-based KPI sheets. `excel/build_native_pivot.py` rebuilds and validates it on Windows with Excel.

## 12. Published retail margin context

Aswath Damodaran's NYU Stern **Margins by Sector (US)** dataset, updated January 2026, reports:

| Sector | Firms | Gross margin | Net margin |
|---|---:|---:|---:|
| Retail (General) | 23 | 33.18% | 5.61% |
| Retail (Grocery and Food) | 15 | 26.31% | 1.32% |
| Retail (Special Lines) | 94 | 35.30% | 5.19% |

Source: [NYU Stern — Margins by Sector (US), January 2026](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html), accessed 27 October 2026.

The project's `(sales − implied cost) / sales` is gross-margin-like **only if** implied cost corresponds to cost of goods sold. It may omit freight/fulfillment included in reported cost of sales and definitely omits operating expense, interest and tax, so the project's 14.43% must **not** be compared with the benchmark net margins. The source has no e-commerce-only sector; these are US company-level, not order-level, benchmarks. Therefore this comparison is context, not a performance verdict.

## Decision

Do not roll the 15% cap out from the fixed-volume scenario alone. Instrument exposure and returns, run the customer-randomized test, and use contribution profit/customer as the decision metric. Use the RFM list for eligibility/stratification, not as evidence that the offers work.
