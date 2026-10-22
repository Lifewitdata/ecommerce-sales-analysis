-- Client-side CSV load for MySQL 8.0.
--
-- Requires: local_infile = ON  (server) and --local-infile=1  (client)
--           secure_file_priv must not block the path, or use LOAD DATA LOCAL
--           as below, which reads from the client and bypasses secure_file_priv.
--
-- Run from the repository root so the relative path resolves:
--   mysql --local-infile=1 -u root -p < sql/load_data.sql
--
-- On Windows, MySQL does not interpret forward slashes in LOAD DATA paths the
-- same way the shell does — pass an absolute path if the load reports 0 rows.

USE ecommerce_sales;

TRUNCATE TABLE orders;

LOAD DATA LOCAL INFILE 'ecommerce_sales.csv'
INTO TABLE orders
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, order_date, customer_id, region, category, sub_category, product,
 quantity, unit_price, discount, sales, profit, payment_method);

-- Sanity check: expect 2,000 rows / 2,000 distinct orders / 573 customers.
SELECT COUNT(*)             AS rows_loaded,
       COUNT(DISTINCT order_id)    AS orders,
       COUNT(DISTINCT customer_id) AS customers,
       ROUND(SUM(sales), 2)        AS revenue,
       ROUND(SUM(profit), 2)       AS profit
FROM orders;
