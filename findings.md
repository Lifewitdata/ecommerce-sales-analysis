# E-commerce sales — findings and recommendations

Two years of order data: **2,000 orders, 573 customers, ₹3.59 Cr revenue, ₹51.8 lakh
profit, 14.43% overall margin** (Jan 2024 – Jun 2025). Every number below is
reproducible — the notebook computes it in pandas and `sql/analysis_queries.sql`
computes the same thing in MySQL; `python sql/verify_sql.py` asserts the two agree
(127 checks).

---

## 1. The business is scaling its thinnest slice

| Category | Revenue share | Profit share | Margin |
|---|---|---|---|
| Electronics | **71.74%** | 44.39% | **8.93%** |
| Home & Kitchen | 10.95% | 18.10% | 23.83% |
| Sports | 10.75% | 21.04% | 28.22% |
| Fashion | 4.22% | 9.06% | 30.95% |
| Beauty | **2.33%** | 7.41% | **45.89%** |

Electronics brings in seven rupees of every ten but less than half of every rupee of
profit. Beauty earns 45.89% on 2.33% of revenue — it is the cheapest growth available
and it is under-marketed. Every rupee of revenue shifted from Electronics to Beauty is
worth ~37 paise of extra profit at these margins.

**Recommendation:** set category-level growth targets in *profit*, not GMV. Any
Electronics spend should be justified against its 8.93% margin, not its topline.

## 2. Discounts past 20% are a subsidy, not a promotion

| Discount | Orders | Avg margin | Total profit | Loss-making orders |
|---|---|---|---|---|
| 0% | 605 | 36.88% | ₹28.6 lakh | 0 |
| 1–10% | 790 | 29.38% | ₹22.7 lakh | 0 |
| 11–20% | 410 | 18.04% | ₹3.0 lakh | 51 |
| 21–30% | 162 | 6.37% | **−₹1.39 lakh** | 36 |
| 30%+ | 33 | **−10.22%** | **−₹1.10 lakh** | 27 |

Margin falls monotonically from 36.88% to −10.22% as the discount rises, and the
crossing point is ~20%, not 30%. Orders discounted above 20% are **195 orders,
₹28.99 lakh of revenue and −₹2.49 lakh of profit** — a −8.58% blended margin, with 63
orders sold below cost.

**Recommendation:** hard-cap blanket discounting at 15% and move the deeper offers to
targeted, margin-aware promotions. Removing the below-cost discounting alone is worth
~₹2.5 lakh of profit, before allowing for any demand response.

## 3. The deep-discount loss is concentrated in one category

| Category | Avg discount | Deep-discounted orders | Profit on those orders |
|---|---|---|---|
| Electronics | 8.78% | 38 | **−₹2.97 lakh** |
| Home & Kitchen | 8.88% | 42 | +₹0.05 lakh |
| Sports | 9.35% | 37 | +₹0.15 lakh |
| Beauty | 8.58% | 31 | +₹0.11 lakh |
| Fashion | 10.34% | 47 | +₹0.17 lakh |

Electronics deep-discounts the *least often* (9.09% of its orders) yet accounts for
**more than the entire company's deep-discount loss** (−₹2.97 lakh vs −₹2.49 lakh
net), because at an 8.93% base margin any discount beyond ~20% is already below cost.
Fashion and Home & Kitchen discount deeper and still stay positive — their base margin
absorbs it.

**Recommendation:** make the discount cap category-aware. A flat "max 20%" rule is
already too loose for Electronics and needlessly tight for Beauty.

## 4. Growth is a seasonal artefact — H1 revenue is actually shrinking

The monthly trend chart peaks at 2024-11 (₹33.2 lakh), which reads as momentum. It
isn't. Comparing like-for-like first halves:

| Period | Orders | Revenue | Margin | AOV |
|---|---|---|---|---|
| H1 2024 | 626 | ₹1.20 Cr | 13.85% | ₹19,140 |
| H1 2025 | 593 | ₹0.98 Cr | **15.47%** | ₹16,485 |

**H1-over-H1 revenue is down 18.41%** and AOV fell 13.9%, while margin improved 1.62pp.
The company is shrinking and getting healthier simultaneously — which is exactly what
you'd expect if volume was being bought with discount depth. The 2024 festive peak is a
season, not a trend, and any target built off it will miss.

**Recommendation:** report H1-vs-H1 and rolling-12-month, never the raw monthly line,
in any growth conversation.

## 5. A loyal top decile carries 41% of revenue

- **88.48%** of customers (507 of 573) order more than once; the heaviest order 10 times.
- The **top 57 customers (10%) generate 41.18% of revenue** — ₹1.48 Cr.
- UPI takes 43.25% of orders; Net Banking is only 7.60% of orders but has the highest AOV
  (₹21,538). Cash on Delivery is just 7.50% of orders.

**Recommendation:** retention budget belongs on the top decile, and the COD share is low
enough that payment-cost savings won't fund the discount cap — margin discipline has to.

## 6. Where margin is best and worst, cell by cell

The category × region heatmap has 20 cells spanning **45.34% (Beauty/North) down to
6.72% (Electronics/West)**. The problem cell is not small: Electronics/West still books
₹49.1 lakh of revenue at 6.72%. Region alone explains little — South leads revenue
(₹1.04 Cr, AOV ₹19,127) but East runs the better margin (15.29% vs 14.73%), and North
has the most orders (571) at the weakest margin (13.51%).

**Recommendation:** the mix, not the map, is the lever. West is not a "bad region";
West is where Electronics is over-weighted.

---

## What I'd do next

1. **Price elasticity per category** — so a discount is priced against its own margin
   instead of applied site-wide.
2. **RFM segmentation** on the 573 customers to operationalise finding #5.
3. **Promo cannibalisation** — measure whether sale weeks steal from full-price weeks
   before funding the next one.
4. **Hypothesis test the 15% cap** as an A/B experiment rather than rolling it out
   company-wide on the strength of an observational slope.

---

*Synthetic dataset (`ecommerce_sales.csv`, 2,000 orders × 13 columns) built to behave
like real retail data — seasonal demand, category margin structure, discount response.
The pipeline and every query work unchanged against live order data.*
