<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:7a2e00,50:ff9966,100:ff5e62&height=180&section=header&text=E-commerce%20Sales%20Analysis&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=38" alt="E-commerce Sales Analysis"/>
</div>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=500&size=20&pause=1000&color=FFA94D&center=true&vCenter=true&width=640&lines=%E2%82%B93.59+Cr+revenue.+But+where%27s+the+profit+leaking%3F;2%2C000+orders+%E2%80%A2+Jan+2024+%E2%80%93+Jun+2025;KPIs+%E2%86%92+deep+dives+%E2%86%92+actions" alt="typing"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="pandas"/>
  <img src="https://img.shields.io/badge/seaborn-4C72B0?style=for-the-badge" alt="seaborn"/>
  <img src="https://img.shields.io/badge/matplotlib-11557C?style=for-the-badge" alt="matplotlib"/>
  <img src="https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white" alt="Jupyter"/>
  <img src="https://img.shields.io/badge/seed_42-deterministic-FFA94D?style=for-the-badge" alt="deterministic"/>
</p>

> **₹3.59 crore in revenue across 2,000 orders** — and a discount policy quietly burning lakhs. This project traces every rupee: which categories earn, which discounts destroy margin, and which customers actually matter.

---

## 📊 The headline numbers

| Metric | Value |
|---|---|
| Orders analyzed | 2,000 (Jan 2024 – Jun 2025) |
| Total revenue | **₹3,59,28,969** |
| Money lost to deep discounting | **~₹2.5 lakh** across 195 orders |
| Revenue from top 10% of customers | **41.2%** |

![monthly trend](visuals/01_monthly_trend.png)

## ⚠️ Finding #1 — the margin-mix trap

Electronics drives **72% of revenue (₹2.58 Cr)** — at an **8.9% margin**. The business is scaling its thinnest slice. Meanwhile Beauty earns **45.9% margin** on just 2% of revenue. Growth without rebalancing is just expensive volume.

![category performance](visuals/02_category_performance.png)

## 🔥 Finding #2 — discounts are subsidizing losses

Orders discounted **21%+ carry negative margins** — the company paid customers to buy. Just 195 such orders burned **~₹2.5 lakh**. The fix isn't subtle: **cap blanket discounting at 15%**, replace site-wide sales with targeted offers.

![discount vs profit](visuals/04_discount_vs_profit.png)

## 👑 Finding #3 — the loyal core

The **top 10% of customers generate 41.2% of revenue**, and UPI dominates payments (43% of orders). Retention spend aimed at this core beats acquisition spend aimed at everyone.

![customer insights](visuals/06_customer_insights.png)

---

## ⚙️ How it works

```mermaid
flowchart LR
    A["🛒 2,000 orders<br/>Jan 2024 – Jun 2025"] --> B["📊 KPIs<br/>revenue · margin · AOV"]
    B --> C["🔍 Deep dives<br/>category · discount · customers"]
    C --> D["💡 Actions<br/>15% cap · rebalance mix"]
    style D fill:#7a2e00,stroke:#FFA94D,stroke-width:2px,color:#fff
```

## 📂 What's inside

```
├── generate_data.py               # synthetic order data, seed 42
├── analysis.py                    # KPIs → deep dives → charts
├── build_notebook.py              # builds the notebook from the pipeline
├── Ecommerce_Sales_Analysis.ipynb # narrated case-study notebook (29 cells)
├── findings.md                    # stakeholder summary
├── data/
│   └── ecommerce_sales.csv        # 2,000 orders × 13 columns
└── visuals/                       # 7 charts (shown above)
```

## ▶️ Run it

```bash
pip install -r requirements.txt
python3 generate_data.py    # build the dataset
python3 analysis.py         # full analysis + 7 charts
```

Or open the notebook — same analysis, narrated step by step. Deterministic: rebuild from scratch, every number reproduces exactly.

---

## 🔭 Where I'd take it next

- **Price elasticity model** — estimate demand response per category so discounts are *priced*, not guessed.
- **RFM segmentation** — recency/frequency/monetary tiers to target the 41.2% core with surgical offers.
- **Promo cannibalization analysis** — do site-wide sales steal from full-price weeks? Measure it before running the next one.

---

*Synthetic order data (seed 42) with realistic retail behavior — seasonal demand, category margin structure, and discount response baked in. Pipeline works identically on live sales data.*

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:7a2e00,50:ff9966,100:ff5e62&height=110&section=footer" alt="footer"/>
</div>
