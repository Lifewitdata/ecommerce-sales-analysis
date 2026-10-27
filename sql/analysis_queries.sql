-- ============================================================================
-- E-commerce sales analysis — MySQL 8.0
--
-- Every query here mirrors a section of Ecommerce_Sales_Analysis.ipynb, so the
-- same findings can be produced in the warehouse instead of pandas. Run them
-- against the `ecommerce_sales.orders` table from sql/schema.sql.
--
-- 13 statements across the 12 analysis sections. All are machine-verified:
--   python sql/verify_sql.py
-- parses each one as MySQL, transpiles it to DuckDB, runs it against the
-- committed CSV and asserts the result against the notebook numbers (127 checks).
--
-- Notation notes:
--   * money columns are DECIMAL, so no float drift on SUM
--   * NULLIF guards every division (no month/category may ever be empty)
--   * margins are reported in percent, rounded to 2 dp
-- ============================================================================

USE ecommerce_sales;


-- Q1  KPI dashboard — the headline numbers
--     Expected: 35,928,968.57 revenue / 5,182,911.58 profit / 14.43% margin
--               2,000 orders / 573 customers / 17,964.48 AOV
SELECT ROUND(SUM(sales),  2)                              AS total_revenue,
       ROUND(SUM(profit), 2)                              AS total_profit,
       ROUND(100 * SUM(profit) / NULLIF(SUM(sales), 0), 2) AS overall_margin_pct,
       COUNT(DISTINCT order_id)                            AS total_orders,
       COUNT(DISTINCT customer_id)                         AS unique_customers,
       ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
       MIN(order_date)                                     AS first_order,
       MAX(order_date)                                     AS last_order
FROM orders;


-- Q2  Monthly revenue / profit / margin trend (notebook 4.1)
--     18 months: 2024-01 .. 2025-06. Peak revenue is 2024-11 (3,322,851.96)
--     at the second-lowest margin of the series (11.88%) — festive volume is
--     the least profitable volume in the business.
SELECT DATE_FORMAT(order_date, '%Y-%m')                  AS order_month,
       ROUND(SUM(sales),  2)                             AS revenue,
       ROUND(SUM(profit), 2)                             AS profit,
       COUNT(DISTINCT order_id)                          AS orders,
       ROUND(100 * SUM(profit) / NULLIF(SUM(sales), 0), 2) AS margin_pct,
       ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS aov
FROM orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month;


-- Q3  Category performance (notebook 4.2) — revenue share vs profit share
--     The whole story is in the two share columns: Electronics is 71.74% of
--     revenue but only 44.39% of profit; Beauty is 2.33% of revenue but 7.41%
--     of profit. Growth in the wrong mix buys volume, not earnings.
WITH cat AS (
  SELECT category,
         SUM(sales)               AS revenue,
         SUM(profit)              AS profit,
         COUNT(DISTINCT order_id) AS orders
  FROM orders
  GROUP BY category
)
SELECT category,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit,  2) AS profit,
       orders,
       ROUND(100 * revenue / NULLIF(SUM(revenue) OVER (), 0), 2) AS revenue_share_pct,
       ROUND(100 * profit  / NULLIF(SUM(profit)  OVER (), 0), 2) AS profit_share_pct,
       ROUND(100 * profit  / NULLIF(revenue, 0), 2)              AS margin_pct,
       ROUND(revenue / NULLIF(orders, 0), 2)                     AS aov
FROM cat
ORDER BY revenue DESC;


-- Q4  Region performance (notebook 4.3)
--     South leads revenue (10,405,345.12) and AOV (19,127.47) but East runs
--     the better margin (15.29% vs 14.73%). North has the most orders (571)
--     and the weakest margin (13.51%) — it is the discount-driven region.
WITH reg AS (
  SELECT region,
         SUM(sales)               AS revenue,
         SUM(profit)              AS profit,
         COUNT(DISTINCT order_id) AS orders
  FROM orders
  GROUP BY region
)
SELECT region,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit,  2) AS profit,
       orders,
       ROUND(revenue / NULLIF(orders, 0), 2)                     AS aov,
       ROUND(100 * profit / NULLIF(revenue, 0), 2)              AS margin_pct,
       ROUND(100 * revenue / NULLIF(SUM(revenue) OVER (), 0), 2) AS revenue_share_pct
FROM reg
ORDER BY revenue DESC;


-- Q5  Discount buckets (notebook 4.4)
--     avg_margin_pct is the mean of per-order margins, exactly as the notebook
--     computes it. It falls 36.88% -> -10.22% as discount rises, and the two
--     deepest buckets are the only ones with negative total profit.
WITH binned AS (
  SELECT order_id,
         discount,
         sales,
         profit,
         CASE WHEN discount <= 0.00 THEN '0%'
              WHEN discount <= 0.10 THEN '1-10%'
              WHEN discount <= 0.20 THEN '11-20%'
              WHEN discount <= 0.30 THEN '21-30%'
              ELSE '30%+' END AS discount_bin,
         CASE WHEN sales > 0 THEN profit / sales ELSE 0 END AS profit_margin
  FROM orders
)
SELECT discount_bin,
       COUNT(*)                                  AS orders,
       ROUND(100 * AVG(profit_margin), 2)        AS avg_margin_pct,
       ROUND(SUM(sales),  2)                     AS revenue,
       ROUND(SUM(profit), 2)                     AS total_profit,
       SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) AS loss_making_orders
FROM binned
GROUP BY discount_bin
ORDER BY MIN(discount);


-- Q6  Top 10 products by revenue (notebook 4.5)
--     AirBook Slim is the #1 earner (8,854,919.38) at a 7.49% margin — the
--     single biggest exposure in the catalogue. Tent 4P and the dumbbell are
--     roughly a third of the revenue at 3-4x the margin.
SELECT product,
       ROUND(SUM(sales),  2) AS revenue,
       ROUND(SUM(profit), 2) AS profit,
       SUM(quantity)         AS units,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(100 * SUM(profit) / NULLIF(SUM(sales), 0), 2) AS margin_pct
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 10;


-- Q7  Customer loyalty and revenue concentration (notebook 4.6)
--     507 of 573 customers order more than once (88.48%), and the top decile
--     (57 customers, matching pandas int(573 * 0.10)) carries 41.18% of revenue.
WITH cust AS (
  SELECT customer_id,
         COUNT(DISTINCT order_id) AS orders,
         SUM(sales)               AS revenue
  FROM orders
  GROUP BY customer_id
)
SELECT COUNT(*)                                              AS customers,
       SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END)           AS repeat_customers,
       ROUND(100 * SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct,
       SUM(CASE WHEN orders >= 5 THEN 1 ELSE 0 END)          AS heavy_customers,
       MAX(orders)                                           AS max_orders_per_customer
FROM cust;


-- Q7b  Revenue share held by the top 10% of customers
WITH cust AS (
  SELECT customer_id,
         SUM(sales) AS revenue
  FROM orders
  GROUP BY customer_id
),
ranked AS (
  SELECT revenue,
         ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rn,
         COUNT(*)     OVER ()                      AS n_customers,
         SUM(revenue) OVER ()                      AS total_revenue
  FROM cust
),
flagged AS (
  SELECT CASE WHEN rn <= FLOOR(n_customers * 0.10) THEN revenue ELSE 0 END AS top_revenue,
         total_revenue
  FROM ranked
)
SELECT ROUND(SUM(top_revenue), 2)                              AS top_decile_revenue,
       ROUND(MAX(total_revenue), 2)                            AS total_revenue,
       ROUND(100 * SUM(top_revenue) / NULLIF(MAX(total_revenue), 0), 2) AS top_decile_share_pct,
       SUM(CASE WHEN top_revenue > 0 THEN 1 ELSE 0 END)        AS customers_in_decile
FROM flagged;


-- Q8  Payment mix (notebook 4.6)
--     UPI takes 43.25% of orders and 15,873,664.36 of revenue; Net Banking is
--     only 7.60% of orders but has the highest AOV (21,538.25). Cash on
--     Delivery — the costliest, most-return-prone method — is just 7.50%.
SELECT payment_method,
       COUNT(*)                                        AS orders,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS order_share_pct,
       ROUND(SUM(sales),  2)                            AS revenue,
       ROUND(SUM(profit), 2)                            AS profit,
       ROUND(SUM(sales) / NULLIF(COUNT(*), 0), 2)       AS aov
FROM orders
GROUP BY payment_method
ORDER BY orders DESC;


-- Q9  Margin heatmap: category x region (notebook 4.7), long form
--     20 cells. Best: Beauty/North at 45.34%. Worst: Electronics/West at 6.72%
--     — and Electronics/West still books 4,913,600.40 of revenue.
SELECT category,
       region,
       COUNT(DISTINCT order_id)  AS orders,
       ROUND(SUM(sales),  2)     AS revenue,
       ROUND(SUM(profit), 2)     AS profit,
       ROUND(100 * AVG(CASE WHEN sales > 0 THEN profit / sales ELSE 0 END), 2) AS avg_margin_pct
FROM orders
GROUP BY category, region
ORDER BY category, region;


-- Q10  The 21%+ discount problem (finding #2, quantified)
--      195 orders, 2,899,323.45 of revenue, -248,884.50 of profit and 63 of
--      them are outright loss-making. That is a -8.58% blended margin: the
--      deeper half of the discount ladder is a subsidy, not a promotion.
SELECT COUNT(DISTINCT order_id)                            AS orders,
       ROUND(SUM(sales),  2)                               AS revenue,
       ROUND(SUM(profit), 2)                               AS profit,
       ROUND(100 * SUM(profit) / NULLIF(SUM(sales), 0), 2) AS margin_pct,
       SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END)         AS loss_making_orders,
       ROUND(AVG(discount) * 100, 2)                       AS avg_discount_pct
FROM orders
WHERE discount > 0.20;


-- Q10b Fixed-volume 15% cap for the same 195 orders; costs held constant.
WITH repriced AS (
  SELECT order_id, sales, profit,
         ROUND(quantity * CAST(unit_price AS DECIMAL(18, 2)) * CAST(0.85 AS DECIMAL(3, 2)), 2)
           AS capped_sales
  FROM orders
  WHERE discount > 0.20
)
SELECT COUNT(*) AS orders,
       ROUND(SUM(sales), 2) AS original_sales,
       ROUND(SUM(profit), 2) AS original_profit,
       ROUND(SUM(capped_sales), 2) AS capped_sales,
       ROUND(SUM(capped_sales - (sales - profit)), 2) AS capped_profit,
       ROUND(SUM(capped_sales - sales), 2) AS profit_difference
FROM repriced;


-- Q11  Like-for-like H1 2024 vs H1 2025 (notebook 4.8)
--      Revenue is DOWN 18.41% year over year (11,981,717.18 -> 9,775,395.76)
--      and AOV fell 19,140.12 -> 16,484.65, while margin improved 13.85% ->
--      15.47%. The business is shrinking and getting healthier at the same
--      time — so "growth" in the headline monthly chart is an artefact of the
--      H2-2024 festive peak, not a trend.
SELECT YEAR(order_date)                 AS calendar_year,
       COUNT(DISTINCT order_id)         AS orders,
       COUNT(DISTINCT customer_id)      AS customers,
       ROUND(SUM(sales),  2)            AS revenue,
       ROUND(SUM(profit), 2)            AS profit,
       ROUND(100 * SUM(profit) / NULLIF(SUM(sales), 0), 2) AS margin_pct,
       ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS aov
FROM orders
WHERE MONTH(order_date) <= 6
GROUP BY YEAR(order_date)
ORDER BY calendar_year;


-- Q12  Where the deep discounting actually happens (links findings #1 and #2)
--      Electronics is only 9.09% deep-discounted but loses 296,669.85 doing it
--      — 119% of the whole company's deep-discount loss. Fashion and Home &
--      Kitchen discount deeper yet stay profitable, because their base margin
--      can absorb it. A blanket discount cap should be category-aware.
SELECT category,
       COUNT(*)                                                     AS orders,
       ROUND(100 * AVG(discount), 2)                                AS avg_discount_pct,
       SUM(CASE WHEN discount > 0.20 THEN 1 ELSE 0 END)             AS deep_discounted_orders,
       ROUND(100 * SUM(CASE WHEN discount > 0.20 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS deep_discount_rate_pct,
       ROUND(SUM(CASE WHEN discount > 0.20 THEN profit ELSE 0 END), 2)
                                                                     AS profit_on_deep_orders,
       ROUND(100 * AVG(CASE WHEN sales > 0 THEN profit / sales ELSE 0 END), 2)
                                                                     AS avg_margin_pct
FROM orders
GROUP BY category
ORDER BY profit_on_deep_orders ASC;
