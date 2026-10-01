# Instacart Customer & Market Basket Analysis

End-to-end analysis of **3.4 million grocery orders** from 206,209 customers — from raw CSVs
through data quality, cleaning, integration, EDA, customer segmentation, reorder analysis and
association rule mining, to a dashboard and an evidence-backed set of business recommendations.

> **Headline:** 59.0% of every item Instacart sells is something that customer has bought
> before. This is a replenishment business, not a discovery business — and the repeat habit is
> built between a customer's 2nd and 6th order.

---

## 1. Project Overview

Instacart is a grocery delivery platform. This project takes its public transaction data and
answers a single commercial question:

> *How do Instacart customers behave, which products matter most to them, and which products
> should be marketed or recommended together?*

The analysis is deliberately written as **business reasoning supported by data**, not as a
tour of techniques. Every chart answers a stated question, every insight cites its evidence,
and every recommendation names the finding it rests on — plus the risk of acting on it.

## 2. Business Problem

| # | Question | Answered in |
|---|---|---|
| 1 | Who are the customers and how do they shop? | notebook 04 · report §6 |
| 2 | Which products and categories matter most? | notebook 05 · report §7 |
| 3 | When do customers buy? | notebook 03 · report §5 |
| 4 | What drives repeat purchase? | notebook 05 · report §8 |
| 5 | Which products are bought together? | notebook 06 · report §9 |
| 6 | What should the business do about it? | report §10–11 |

## 3. Dataset

**Instacart Online Grocery Shopping Dataset 2017** — six CSV files, ~700 MB.

| File | Rows | Grain |
|---|---:|---|
| `orders.csv` | 3,421,083 | one order |
| `order_products__prior.csv` | 32,434,489 | product × order (full history) |
| `order_products__train.csv` | 1,384,617 | product × order (most recent order of 131,209 customers) |
| `products.csv` | 49,688 | one product |
| `aisles.csv` | 134 | one aisle |
| `departments.csv` | 21 | one department |

Place the six CSVs in `data/raw/` (or symlink them there — see *Reproducing*).

## 4. Data Structure

```
 departments (21) ──┐
                    ├──> products (49,688) ──> order_products (33.8M lines)
 aisles (134) ──────┘                                 ^
                                                      │
                              orders (3.42M) ─────────┘
                                user_id   ← no customer table exists
```

Two structural facts shaped everything:

- **There is no customer table.** Every customer attribute (order count, basket size, reorder
  rate, interval, segment) is *derived* from order history. Demographic segmentation was never
  an option.
- **75,000 orders have no contents** (the withheld `test` split). They are excluded from
  item-level analysis and kept for order-timing analysis. Every table in this project names
  its base: **all orders (3,421,083)** for timing, **orders with contents (3,346,083)** for
  anything item-level.

## 5. Methodology

| Phase | What was done | Notebook |
|---|---|---|
| 1 · Data understanding | Data dictionary, data model, key & referential-integrity checks, quality report | `01` |
| 2 · Cleaning | 4 reasoned decisions, **0 rows deleted, 0 values imputed** | `02` |
| 3 · Integration | Customer → Order → Order Product → Product → Aisle → Department; aggregate-before-join; row-count verification on every join | `02` |
| 4 · KPIs | Overall, product, department and aisle KPIs | `03` |
| 5 · Customer analysis | Frequency, basket size, K-Means segmentation on 3 behavioural dimensions | `04` |
| 6 · Time analysis | Hour, day of week, day×hour, inter-order interval | `03` |
| 7–8 · Product & category | Top products, volume × loyalty quadrants, department/aisle performance | `05` |
| 9 · Reorder analysis | By order number, tenure, cart position, category; variance decomposition | `05` |
| 10 · Market basket | FP-Growth at product and aisle level, with justified thresholds | `06` |
| 11–12 · Insight & recommendation | Finding → Evidence → Business meaning; 6 recommendations | `reports/final_report.md` |

**Three methodological choices worth highlighting:**

1. **Nothing was deleted.** The dataset has zero orphan foreign keys, zero duplicate rows and
   zero invalid codes. What it needed was *interpretation* — the 206,209 nulls in
   `days_since_prior_order` all sit on first orders and mean "no previous order exists", so
   they were flagged, never imputed.
2. **Reorder-rate rankings always carry a minimum-volume threshold.** A product with 12
   purchases and a 50% reorder rate is noise. Thresholds are stated wherever a ranking appears.
3. **The segmentation is presented as a judgement, not a discovery.** Silhouette peaks at
   k = 2 (0.365) and never exceeds 0.37 — this customer base is a continuum. k = 4 was chosen
   because it separates two independent growth levers into actionable groups, and that
   reasoning is stated rather than hidden.

## 6. Tools

`Python 3.13` · `pandas` · `NumPy` · `Matplotlib` · `scikit-learn` (K-Means, StandardScaler)
· `MLxtend` (FP-Growth, association rules) · `SciPy` (sparse matrices) · `XlsxWriter`
(dashboard) · `ReportLab` (PDF) · `Jupyter`

## 7. Key Findings

1. **59.0% of all items sold are reorders** (62.9% excluding first orders, which structurally
   cannot contain one). This is a replenishment business.
2. **The habit forms between orders 2 and 6** — reorder rate climbs 27.2% → 54.1% there, then
   flattens (81.9% by order 50). Retention spend after order 10 is largely redundant.
3. **Order frequency and basket size are uncorrelated** (ρ = 0.06). They are two independent
   levers; reorder rate (ρ = 0.73) and interval (ρ = −0.60) are what actually track loyalty.
4. **Customers run on a weekly clock** — 50.9% of repeat orders within 7 days, with a clear
   spike at exactly day 7.
5. **Produce drives traffic (29.2% of units, 74.9% basket penetration); dairy drives return**
   (67.0% reorder rate, the highest of any department).
6. **Reorder rate is a consumption-cadence meter, not a satisfaction score** — aisle explains
   56.3% of the variance. Spices at 15.3% is normal; benchmark within category, never against
   the 59% average.
7. **The real cross-sell signals are culinary** — garlic↔onion (lift 5.64), pasta↔pasta sauce
   (4.41), lime↔lemon (4.08) — **while bananas, in 14.7% of baskets, predict nothing** yet are
   the consequent of 21.5% of all mined rules.
8. **17.1% of orders hold ≤3 items but only 3.5% of units**, and these have the *highest*
   reorder rate (65.0%) — forgotten-essentials top-ups, not a problem to suppress.

### Customer segments

| Segment | Customers | % of items | Orders | Basket | Reorder | Interval |
|---|---:|---:|---:|---:|---:|---:|
| Loyal Regulars | 44,475 (21.6%) | **53.4%** | 40.6 | 10.1 | 69.0% | 8.8 d |
| Big-Basket Stockers | 33,020 (16.0%) | 20.6% | 10.6 | 19.4 | 46.2% | 16.9 d |
| Steady Small-Basket | 62,996 (30.5%) | 17.1% | 12.9 | 7.0 | 49.3% | 15.6 d |
| Occasional / At-Risk | 65,718 (31.9%) | 8.9% | 5.7 | 8.0 | 22.3% | 19.1 d |

## 8. Business Recommendations

Full reasoning, measurement plan and risks for each in `reports/final_report.md` §11
(Indonesian: `reports/final_report_ID.md` §11).

| # | Recommendation | Rests on |
|---|---|---|
| **R1** | Launch replenishment subscriptions, seeded from the milk & yogurt cluster | 9 of the top 10 reorder rates are milk (83.9–86.1%); milk aisle 78.2% |
| **R2** | Concentrate retention spend on orders 2–6 | reorder rate 27.2% → 54.1% in that window, then flat |
| **R3** | Treat the two middle segments as two different problems | frequency ⟂ basket size (ρ = 0.06); 7.0 vs 19.4 items at the same order count |
| **R4** | Build basket-completion prompts on recipe pairs, not popularity | garlic↔onion 5.64, pasta↔sauce 4.41; bananas = 21.5% of rules, zero information |
| **R5** | Set service levels by quadrant; benchmark reorder rate within category | 2,537 core staples = 67.5% of units; aisle explains 56.3% of reorder variance |
| **R6** | Time campaigns to the two differently-shaped weekend peaks | days 0–1 = 34.7% of the week but peak at 13:00–15:00 vs 09:00–11:00 |

## 9. Dashboard

`dashboard/instacart_dashboard.xlsx` — a one-page Excel dashboard with 12 charts:

- **KPI tiles** — customers, orders, items, average basket, reorder rate
- **When do customers buy?** — orders by hour, by day of week, by inter-order interval
- **What do they buy?** — top products, highest reorder rates, department share
- **Who repeats, and when?** — habit curve, reorder by tenure, segment size vs value
- **What sells together?** — aisle pairings by lift, product quadrants, aisle reorder rates

Each section carries a written **insight callout**, not just charts. Seven filterable explorer
tabs (`Rules (product)`, `Rules (aisle)`, `Products`, `Departments`, `Aisles`, `Segments`,
`KPIs`) sit behind it, plus a `Data index` tab documenting measurement bases and known limits.

`dashboard/powerbi_model/` holds the same data as a dimensional model
(`dim_*` / `fact_*` CSVs) ready to load straight into Power BI.

## 10. Project Structure

```
.
├── data/
│   ├── raw/                     six source CSVs (symlinked to archive/)
│   └── processed/               cleaned + integrated parquet tables
├── notebooks/
│   ├── 01_data_understanding.ipynb      data dictionary, model, quality report
│   ├── 02_data_cleaning.ipynb           cleaning decisions + integration
│   ├── 03_eda.ipynb                     KPIs + time analysis
│   ├── 04_customer_analysis.ipynb       frequency, basket size, segmentation
│   ├── 05_product_analysis.ipynb        products, categories, reorder behaviour
│   ├── 06_market_basket_analysis.ipynb  FP-Growth association rules
│   └── _src/                            notebook sources (plain .py, executed into .ipynb)
├── src/
│   ├── instacart.py             paths, loaders, chart styling
│   ├── analysis.py              Phase 4–9 analysis functions
│   ├── mba.py                   Phase 10 market basket functions
│   ├── build_clean.py           the cleaning + integration pipeline
│   ├── build_dashboard.py       Excel dashboard + Power BI model
│   ├── md2pdf.py                report PDF renderer
│   ├── py2nb.py                 builds and executes the notebooks
│   └── verify_report.py         re-checks all 40 figures quoted in the report/README
├── reports/
│   ├── final_report.md / .pdf      the written report (English)
│   ├── final_report_ID.md / .pdf   the same report in Indonesian
│   ├── figures/                 23 charts
│   ├── tables/                  23 supporting CSVs
│   └── cleaning_log.json        full audit trail of every cleaning decision
├── dashboard/
│   ├── instacart_dashboard.xlsx
│   └── powerbi_model/
└── README.md
```

## 11. Reproducing

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install pandas numpy matplotlib seaborn scikit-learn mlxtend \
    openpyxl xlsxwriter pyarrow jupyter nbclient ipykernel reportlab
```

Put the six CSVs in `data/raw/`, then:

```bash
.venv/bin/python src/build_clean.py        # clean + integrate -> data/processed/
.venv/bin/python src/build_dashboard.py    # Excel dashboard + Power BI model
```

To re-run the notebooks end to end (each is executed, with outputs, from its `.py` source):

```bash
for n in 01_data_understanding 02_data_cleaning 03_eda 04_customer_analysis 05_product_analysis 06_market_basket_analysis; do
  .venv/bin/python src/py2nb.py "notebooks/_src/$n.py" "notebooks/$n.ipynb"
done
```

Full run is roughly 25 minutes and peaks around 4 GB of RAM (the fact table is 33.8M rows).

Afterwards, confirm the written documents still match the data:

```bash
.venv/bin/python src/verify_report.py   # 40 headline figures, exits non-zero on drift
```

## 12. Conclusion

Instacart's customers are **habitual, weekly, daytime shoppers** who mostly re-buy what they
already know. The commercial opportunity is therefore less about recommending new things and
more about **making the known list effortless, and intervening in the narrow window where the
habit is still forming**.

The three levers the data supports most strongly are **replenishment automation** on the
high-cadence dairy cluster, **onboarding through orders 2–6**, and **recipe-shaped basket
completion** in place of popularity-ranked recommendations.

**What this dataset cannot support:** there are no prices, margins, dates or demographics.
No revenue figure appears anywhere in this project, seasonality cannot be measured, and every
bundle recommendation is explicitly conditional on a margin check this data cannot perform.
Those limits are stated wherever they bite rather than being quietly stepped over.

---

*Dataset: Instacart Online Grocery Shopping Dataset 2017, released by Instacart under a
non-commercial research licence. Day-of-week names used in this project are an assumption —
the source does not document the 0–6 mapping — and no conclusion depends on them.*
