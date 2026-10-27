"""Verify sql/analysis_queries.sql — every MySQL query, against the CSV.

There is no MySQL server in CI or on a laptop, so this proves the SQL two other
ways:

  1. sqlglot parses each query with the *MySQL* dialect. If a construct is not
     valid MySQL 8.0, this fails here (not silently in production).
  2. Each query is transpiled MySQL -> DuckDB and executed against the committed
     ecommerce_sales.csv, then every number is asserted against the value the
     notebook computed with pandas.

Run:  python sql/verify_sql.py       (exit 0 = all checks pass)

Expected values live in EXPECTED below; they were produced by the notebook's own
pandas code, not typed from the README.
"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd
import sqlglot

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "ecommerce_sales.csv"
SQL_FILE = Path(__file__).resolve().parent / "analysis_queries.sql"

MYSQL_DIALECT = "mysql"
TARGET_DIALECT = "duckdb"

ok = True
checks = 0


def check(name, actual, expected, tol=None):
    global ok, checks
    checks += 1
    if tol is None:
        good = actual == expected
    else:
        good = actual is not None and abs(float(actual) - expected) <= tol * max(1.0, abs(expected))
    print(("PASS " if good else "FAIL ") + f"{name}: sql={actual} expected={expected}")
    ok = ok and good


# ---------------------------------------------------------------- load queries
raw = SQL_FILE.read_text(encoding="utf-8")
raw = "\n".join(line for line in raw.splitlines()
                if not line.strip().upper().startswith("USE "))

markers = [(m.group(1), m.start()) for m in re.finditer(r"^-- (Q\w+)\b", raw, re.M)]
markers.append((None, len(raw)))

QUERIES = {}
for (qid, start), (_, end) in zip(markers, markers[1:]):
    chunk = raw[start:end]
    body = re.search(r"(?:^|\n)(WITH|SELECT)\b", chunk)
    if not body:
        continue
    text = chunk[body.start():].strip().rstrip(";").strip()
    QUERIES[qid.upper()] = text

print(f"parsed {len(QUERIES)} queries: {', '.join(sorted(QUERIES, key=lambda q: (len(q), q)))}\n")


# ---------------------------------------------------------------- build table
con = duckdb.connect()
con.execute(
    f"""
    CREATE TABLE orders AS
    SELECT * FROM read_csv_auto('{CSV.as_posix()}')
    """
)
con.execute("UPDATE orders SET order_date = CAST(order_date AS DATE)")


def run(qid, label=None):
    """Transpile the MySQL text to DuckDB and execute it."""
    sql = QUERIES[qid]
    try:
        sqlglot.parse_one(sql, read=MYSQL_DIALECT)
    except Exception as exc:  # noqa: BLE001 - report, do not crash the harness
        raise AssertionError(f"{qid} is not parseable as MySQL: {exc}") from exc
    transpiled = sqlglot.transpile(sql, read=MYSQL_DIALECT, write=TARGET_DIALECT)[0]
    try:
        rows = con.execute(transpiled).fetchall()
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"{qid} ({label or ''}) failed to run on DuckDB: {exc}\n{transpiled}"
        ) from exc
    return rows


# ============================================================ Q1 KPI dashboard
q1 = run("Q1", "KPI dashboard")[0]
check("Q1 total_revenue", q1[0], 35928968.57, tol=0.0001)
check("Q1 total_profit", q1[1], 5182911.58, tol=0.0001)
check("Q1 overall_margin_pct", q1[2], 14.43, tol=0.001)
check("Q1 total_orders", q1[3], 2000)
check("Q1 unique_customers", q1[4], 573)
check("Q1 avg_order_value", q1[5], 17964.48, tol=0.001)
check("Q1 first_order", str(q1[6]), "2024-01-01")
check("Q1 last_order", str(q1[7]), "2025-06-30")

# ============================================================= Q2 monthly trend
q2 = run("Q2", "monthly trend")
check("Q2 month count", len(q2), 18)
check("Q2 first month", q2[0][0], "2024-01")
check("Q2 last month", q2[-1][0], "2025-06")
check("Q2 2024-01 revenue", q2[0][1], 1262656.83, tol=0.001)
check("Q2 2024-01 margin_pct", q2[0][4], 18.04, tol=0.001)
check("Q2 orders sum", sum(row[3] for row in q2), 2000)
check("Q2 revenue sum", round(sum(row[1] for row in q2), 2), 35928968.57, tol=0.001)
peak = max(q2, key=lambda row: row[1])
check("Q2 peak revenue month", peak[0], "2024-11")
check("Q2 peak revenue", peak[1], 3322851.96, tol=0.001)
check("Q2 peak margin_pct", peak[4], 11.88, tol=0.001)
worst = min(q2, key=lambda row: row[4])
check("Q2 thinnest margin month", worst[0], "2024-02")
check("Q2 thinnest margin_pct", worst[4], 8.08, tol=0.001)

# =========================================================== Q3 category mix
q3 = run("Q3", "category performance")
check("Q3 category count", len(q3), 5)
check("Q3 revenue_share sums to 100", round(sum(row[4] for row in q3), 1), 100.0, tol=0.05)
check("Q3 profit_share sums to 100", round(sum(row[5] for row in q3), 1), 100.0, tol=0.05)
check("Q3 top category", q3[0][0], "Electronics")
check("Q3 Electronics revenue", q3[0][1], 25774936.06, tol=0.001)
check("Q3 Electronics revenue_share_pct", q3[0][4], 71.74, tol=0.001)
check("Q3 Electronics profit_share_pct", q3[0][5], 44.39, tol=0.001)
check("Q3 Electronics margin_pct", q3[0][6], 8.93, tol=0.001)
beauty = next(row for row in q3 if row[0] == "Beauty")
check("Q3 Beauty revenue_share_pct", beauty[4], 2.33, tol=0.001)
check("Q3 Beauty profit_share_pct", beauty[5], 7.41, tol=0.001)
check("Q3 Beauty margin_pct", beauty[6], 45.89, tol=0.001)

# =============================================================== Q4 regions
q4 = run("Q4", "region performance")
check("Q4 region count", len(q4), 4)
check("Q4 top region", q4[0][0], "South")
check("Q4 South revenue", q4[0][1], 10405345.12, tol=0.001)
check("Q4 South orders", q4[0][3], 544)
check("Q4 South aov", q4[0][4], 19127.47, tol=0.001)
check("Q4 South margin_pct", q4[0][5], 14.73, tol=0.001)
east = next(row for row in q4 if row[0] == "East")
check("Q4 East margin_pct", east[5], 15.29, tol=0.001)
north = next(row for row in q4 if row[0] == "North")
check("Q4 North orders", north[3], 571)
check("Q4 North margin_pct", north[5], 13.51, tol=0.001)
check("Q4 revenue_share sums to 100", round(sum(row[6] for row in q4), 1), 100.0, tol=0.05)

# ========================================================= Q5 discount buckets
q5 = run("Q5", "discount buckets")
check("Q5 bucket count", len(q5), 5)
check("Q5 orders sum", sum(row[1] for row in q5), 2000)
bins = {row[0]: row for row in q5}
for name, orders, margin, profit, losses in [
    ("0%", 605, 36.88, 2860137.89, 0),
    ("1-10%", 790, 29.38, 2267746.79, 0),
    ("11-20%", 410, 18.04, 303911.40, 51),
    ("21-30%", 162, 6.37, -139268.55, 36),
    ("30%+", 33, -10.22, -109615.95, 27),
]:
    row = bins[name]
    check(f"Q5 {name} orders", row[1], orders)
    check(f"Q5 {name} avg_margin_pct", row[2], margin, tol=0.001)
    check(f"Q5 {name} total_profit", row[4], profit, tol=0.001)
    check(f"Q5 {name} loss_making_orders", row[5], losses)
check("Q5 margin falls monotonically with discount",
      [round(r[2], 2) for r in q5] == sorted([round(r[2], 2) for r in q5], reverse=True), True)

# ========================================================== Q6 top products
q6 = run("Q6", "top products")
check("Q6 row count", len(q6), 10)
check("Q6 #1 product", q6[0][0], "AirBook Slim")
check("Q6 #1 revenue", q6[0][1], 8854919.38, tol=0.001)
check("Q6 #1 profit", q6[0][2], 662939.48, tol=0.001)
check("Q6 #1 units", q6[0][3], 125)
check("Q6 #1 margin_pct", q6[0][5], 7.49, tol=0.001)
check("Q6 revenue desc order", [row[1] for row in q6] == sorted([row[1] for row in q6], reverse=True), True)
check("Q6 top10 revenue share",
      round(100 * sum(row[1] for row in q6) / 35928968.57, 2), 84.66, tol=0.05)

# ====================================================== Q7 customer loyalty
q7 = run("Q7", "repeat rate")[0]
check("Q7 customers", q7[0], 573)
check("Q7 repeat_customers", q7[1], 507)
check("Q7 repeat_rate_pct", q7[2], 88.48, tol=0.001)
check("Q7 heavy_customers", q7[3], 142)
check("Q7 max_orders_per_customer", q7[4], 10)

q7b = run("Q7B", "top decile concentration")[0]
check("Q7b customers_in_decile", q7b[3], 57)
check("Q7b top_decile_revenue", q7b[0], 14796753.19, tol=0.001)
check("Q7b total_revenue", q7b[1], 35928968.57, tol=0.001)
check("Q7b top_decile_share_pct", q7b[2], 41.18, tol=0.001)

# ========================================================= Q8 payment mix
q8 = run("Q8", "payment mix")
check("Q8 method count", len(q8), 5)
check("Q8 orders sum", sum(row[1] for row in q8), 2000)
pay = {row[0]: row for row in q8}
check("Q8 top method", q8[0][0], "UPI")
check("Q8 UPI orders", pay["UPI"][1], 865)
check("Q8 UPI order_share_pct", pay["UPI"][2], 43.25, tol=0.001)
check("Q8 UPI revenue", pay["UPI"][3], 15873664.36, tol=0.001)
check("Q8 Net Banking aov", pay["Net Banking"][5], 21538.25, tol=0.001)
check("Q8 COD order_share_pct", pay["Cash on Delivery"][2], 7.50, tol=0.001)
check("Q8 order_share sums to 100", round(sum(row[2] for row in q8), 1), 100.0, tol=0.05)

# ====================================================== Q9 margin heatmap
q9 = run("Q9", "category x region heatmap")
check("Q9 cell count", len(q9), 20)
check("Q9 orders sum", sum(row[2] for row in q9), 2000)
cells = {(row[0], row[1]): row for row in q9}
check("Q9 best cell Beauty/North margin_pct", cells[("Beauty", "North")][5], 45.34, tol=0.001)
check("Q9 worst cell Electronics/West margin_pct", cells[("Electronics", "West")][5], 6.72, tol=0.001)
check("Q9 Electronics/West revenue", cells[("Electronics", "West")][3], 4913600.40, tol=0.001)
best_cell = max(q9, key=lambda row: row[5])
worst_cell = min(q9, key=lambda row: row[5])
check("Q9 argmax cell", (best_cell[0], best_cell[1]), ("Beauty", "North"))
check("Q9 argmin cell", (worst_cell[0], worst_cell[1]), ("Electronics", "West"))

# ================================================== Q10 deep discount damage
q10 = run("Q10", "21%+ discount damage")[0]
check("Q10 orders", q10[0], 195)
check("Q10 revenue", q10[1], 2899323.45, tol=0.001)
check("Q10 profit", q10[2], -248884.50, tol=0.001)
check("Q10 margin_pct", q10[3], -8.58, tol=0.001)
check("Q10 loss_making_orders", q10[4], 63)
check("Q10 avg_discount_pct", q10[5], 29.05, tol=0.001)

q10b = run("Q10B", "fixed-volume 15% cap")[0]
check("Q10b orders", q10b[0], 195)
for index, name, expected in [(1, "original_sales", 2899323.45),
                              (2, "original_profit", -248884.50),
                              (3, "capped_sales", 3475106.40),
                              (4, "capped_profit", 326898.45),
                              (5, "profit_difference", 575782.95)]:
    check(f"Q10b {name}", q10b[index], expected, tol=1e-10)

# ======================================================== Q11 H1 vs H1 YoY
q11 = run("Q11", "H1 like-for-like")
check("Q11 year count", len(q11), 2)
y24, y25 = q11[0], q11[1]
check("Q11 2024 orders", y24[1], 626)
check("Q11 2024 revenue", y24[3], 11981717.18, tol=0.001)
check("Q11 2024 margin_pct", y24[5], 13.85, tol=0.001)
check("Q11 2024 aov", y24[6], 19140.12, tol=0.001)
check("Q11 2025 orders", y25[1], 593)
check("Q11 2025 revenue", y25[3], 9775395.76, tol=0.001)
check("Q11 2025 margin_pct", y25[5], 15.47, tol=0.001)
check("Q11 2025 aov", y25[6], 16484.65, tol=0.001)
check("Q11 H1 revenue YoY pct", round(100 * (y25[3] / y24[3] - 1), 2), -18.41, tol=0.01)

# ============================================ Q12 deep discount by category
q12 = run("Q12", "deep discount by category")
check("Q12 category count", len(q12), 5)
check("Q12 orders sum", sum(row[1] for row in q12), 2000)
check("Q12 deep orders sum", sum(row[3] for row in q12), 195)
check("Q12 worst category", q12[0][0], "Electronics")
check("Q12 Electronics deep_discounted_orders", q12[0][3], 38)
check("Q12 Electronics deep_rate_pct", q12[0][4], 9.09, tol=0.001)
check("Q12 Electronics profit_on_deep_orders", q12[0][5], -296669.85, tol=0.001)
check("Q12 profit_on_deep ascending",
      [row[5] for row in q12] == sorted([row[5] for row in q12]), True)
check("Q12 Electronics loss is majority of total",
      q12[0][5] < -248884.50, True)

# ==================================================== cross-check vs pandas
print()
df = pd.read_csv(CSV, parse_dates=["order_date"])
pandas_margin = {c: round(100 * g["profit"].sum() / g["sales"].sum(), 2)
                 for c, g in df.groupby("category")}
for row in q3:
    check(f"Q3 {row[0]} margin agrees with pandas", row[6], pandas_margin[row[0]], tol=0.02)

print()
print(f"{checks} checks run, {'ALL PASS' if ok else 'FAILURES PRESENT'}")
sys.exit(0 if ok else 1)
