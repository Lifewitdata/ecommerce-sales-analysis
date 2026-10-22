-- MySQL 8.0 schema for the e-commerce sales dataset.
--
--   mysql -u root -p < sql/schema.sql
--   mysql --local-infile=1 -u root -p < sql/load_data.sql
--
-- One row = one order line. `order_id` is unique in this dataset (2,000 rows,
-- 2,000 distinct order_ids), so it is safe as the primary key.

CREATE DATABASE IF NOT EXISTS ecommerce_sales
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ecommerce_sales;

DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
  order_id        VARCHAR(12)     NOT NULL,
  order_date      DATE            NOT NULL,
  customer_id     VARCHAR(10)     NOT NULL,
  region          VARCHAR(20)     NOT NULL,
  category        VARCHAR(30)     NOT NULL,
  sub_category    VARCHAR(30)     NOT NULL,
  product         VARCHAR(60)     NOT NULL,
  quantity        SMALLINT        NOT NULL,
  unit_price      DECIMAL(12, 2)  NOT NULL,
  discount        DECIMAL(4, 2)   NOT NULL,
  sales           DECIMAL(14, 2)  NOT NULL,
  profit          DECIMAL(14, 2)  NOT NULL,
  payment_method  VARCHAR(20)     NOT NULL,
  PRIMARY KEY (order_id),
  KEY idx_order_date (order_date),
  KEY idx_category   (category),
  KEY idx_region     (region),
  KEY idx_customer   (customer_id)
) ENGINE = InnoDB;
