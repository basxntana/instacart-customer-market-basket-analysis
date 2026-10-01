# Instacart Customer & Market Basket Analysis
### Final Report

**Role:** Data Analyst · **Dataset:** Instacart Online Grocery Shopping Dataset 2017

**Scope:** 206,209 customers · 3,421,083 orders · 33,819,106 purchased items · 49,688 products

---

## 1. Executive Summary

Instacart's transaction data describes a **replenishment business, not a discovery business**.
**59.0% of every item sold is something that customer has bought before**, and that single
figure determines where the commercial opportunity sits.

Six findings carry the analysis:

1. **The repeat habit is built between a customer's 2nd and 6th order.** Reorder rate climbs
   from 27.2% to 54.1% across that window and then flattens. Retention effort spent after
   order 10 is spent on customers who are already retained.
2. **Order frequency and basket size are statistically unrelated** (Spearman ρ = 0.06). They
   are two independent growth levers, and treating "engagement" as one number conflates them.
3. **Customers run on a weekly clock.** 50.9% of repeat orders arrive within 7 days, with a
   distinct spike exactly at day 7 — a non-arbitrary trigger point that the business did not
   have to invent.
4. **Produce drives traffic; dairy drives the return visit.** Produce is 29.2% of units and
   reaches 74.9% of baskets, but dairy & eggs has the highest reorder rate of any department
   (67.0%).
5. **Reorder rate is a consumption-cadence meter, not a satisfaction score.** Category
   explains 56.3% of the variance in a product's reorder rate. Olive oil's 47.7% is healthy;
   a milk at 47.7% would be alarming.
6. **The best cross-sell signals are culinary, and the best-selling product is useless as a
   recommendation.** Garlic↔onion (lift 5.64) and pasta↔pasta sauce (lift 4.41) are real;
   bananas appear in 14.7% of baskets and therefore predict nothing — yet they are the
   consequent of 21.5% of all mined rules.

Six recommendations follow in §11, each tied to the evidence above. The highest-value one
is a **replenishment subscription seeded from the milk and yogurt cluster**, where the
behaviour already exists at an 84–86% reorder rate and the product is only being asked to
stop making the customer retype it.

**What this dataset cannot tell us:** there are no prices, margins, dates or demographics.
No revenue figure appears anywhere in this report, and seasonality cannot be measured.

---

## 2. Business Problem

> *How do Instacart customers behave, which products matter most to them, and which products
> should be marketed or recommended together?*

Broken into the questions the analysis had to answer:

| # | Question | Where answered |
|---|---|---|
| 1 | Who are the customers and how do they shop? | §6 |
| 2 | Which products and categories matter most? | §7 |
| 3 | When do customers buy? | §5 |
| 4 | What drives repeat purchase? | §8 |
| 5 | Which products are bought together? | §9 |
| 6 | What commercial opportunities follow? | §10–11 |

---

## 3. Dataset

Six tables, in a star-shaped schema with one large fact table split across two files.

| Table | Rows | Grain | Role |
|---|---|---|---|
| `orders` | 3,421,083 | one order | fact header — customer, sequence, day, hour, interval |
| `order_products__prior` | 32,434,489 | product × order | basket contents, full history |
| `order_products__train` | 1,384,617 | product × order | basket contents, most recent order of 131,209 customers |
| `products` | 49,688 | one product | dimension; carries both aisle and department keys |
| `aisles` | 134 | one aisle | dimension |
| `departments` | 21 | one department | dimension |

```
 departments (21) ──┐
                    ├──> products (49,688) ──> order_products (33.8M lines)
 aisles (134) ──────┘                               ^
                                                    │
                            orders (3.42M) ─────────┘
                              user_id  (no customer table exists)
```

**Two structural facts shaped the whole project.**

*There is no customer table.* Every customer attribute in this report — order count, average
basket, reorder rate, interval, segment — was derived from order history. Demographic
segmentation was never an option.

*75,000 orders have no contents.* The `test` orders were withheld in the original Kaggle
release. They are excluded from all item-level analysis and retained for order-timing
analysis, where their fields are valid. Every table in this report names its base:

- **all orders (3,421,083)** — timing, frequency, interval
- **orders with contents (3,346,083)** — products, categories, baskets, reorder rate

---

## 4. Data Preparation

### 4.1 Data quality

The dataset is unusually clean: **zero orphan foreign keys, zero duplicate rows, zero
invalid codes**, and the composite key `(order_id, product_id)` is unique in both basket
files. **No row was deleted and no value was imputed in this entire project.**

What it needed was interpretation, not repair. Four fields are easy to misread:

| # | Issue | Decision | Reasoning |
|---|---|---|---|
| 1 | 206,209 nulls in `days_since_prior_order` | kept as null + `is_first_order` flag | Every null sits on `order_number = 1` and the count equals the customer count exactly. The null means "no previous order exists". Imputing 0 would invent 206,209 same-day repeat purchases. |
| 2 | `days_since_prior_order` capped at 30 (10.8% of orders) | flagged `dspo_is_capped`; interval reported both ways | 369,323 orders sit at exactly 30 against 18,418 at 29 — a 20× cliff no behaviour produces. "30" means "at least 30". |
| 3 | 99 product names shared by multiple `product_id`s | added `product_uid` merging same-name-same-aisle ids | 'BBQ Sauce' and 'Bbq Sauce' are one shelf item listed twice. Split, it ranked #12,002; merged, #9,842. Only 0.23% of the catalogue is affected, and `product_id` was left untouched. |
| 4 | `missing` / `other` placeholder categories (1,258 products) | flagged `is_placeholder`; kept in totals, excluded from rankings | An "unknown" bucket must never win a top-category ranking. |

Also carried forward: `order_number` is capped at 100 (1,374 customers sit on it), and
`order_dow` has **no documented day mapping** — day names in this report are a stated
assumption, and no conclusion depends on them.

**Outliers were examined and kept.** The largest basket is 145 items and the busiest
customer has 100 orders. Both are plausible grocery behaviour, and removing them would
delete exactly the high-value behaviour the project exists to explain.

### 4.2 Integration

The required chain — Customer → Order → Order Product → Product → Aisle → Department — was
built with one governing rule: **aggregate before joining.** Joining 33.8M basket lines onto
3.42M orders would fan the order table out to 33.8M rows and silently weight every
order-level average by basket size. Basket size was therefore aggregated to order grain
first, then joined back.

**Every join changed the row count by exactly zero**, which is the test that a many-to-one
join on a primary key is correct. A left join (not inner) preserved the 75,000 test orders
with a null basket size rather than dropping them.

---

## 5. Exploratory Analysis — When Customers Buy

**Hour.** 64.9% of all orders are placed between 09:00 and 16:00, peaking at 10:00 (288,418
orders). Overnight (00:00–05:00) is 1.8%. But **the busiest hour is not the biggest-basket
hour**: 21:00–23:00 carries only 5.3% of orders and the largest baskets of the day
(10.7–11.0 items vs 10.1 overall).

**Day.** Days 0 and 1 carry 34.7% of the week (600,905 + 587,478 orders); the quietest day
carries 12.5%. Peak-to-trough is only 1.41×. Critically, **the two peak days have different
shapes** — day 0 peaks 13:00–15:00 with 11.2-item baskets, day 1 peaks 09:00–11:00 with
10.2. A single weekend campaign sent at one time misses one of them.

**Interval.** 50.9% of repeat orders arrive within 7 days, and day 7 is a visible spike
(10.0% of repeat orders, against 7.5% at day 6 and 5.7% at day 8), with secondary bumps at
14, 21 and 30. **Customers run a weekly shop.**

The interval also predicts basket composition: reorder rate is **65.8%** for orders placed
within 3 days and **48.0%** after 25+ days. A customer returning after a week wants their
usual list; one returning after a month is rebuilding the habit.

**Cart position.** Reorder rate falls from **67.9% at cart position 1** to 51.0% at position
15. Customers add their habits first and browse later — which is a direct instruction about
where in a session discovery belongs.

---

## 6. Customer Analysis

**Frequency.** Median 10 orders per customer, mean 16.6 (skew 2.4). Concentration is real
but moderate: the top 10% of customers buy **35.1%** of items, the top 20% buy **53.7%**.
This is *not* an 80/20 business — the bottom half still accounts for 17.8% of volume.

**The key negative result.** Order frequency and basket size are **uncorrelated**
(ρ = 0.06). What *does* move with order count is reorder rate (ρ = 0.73) and, negatively,
interval (ρ = −0.60). Across order bands, basket size moves only 9.6 → 10.4 items while
reorder rate moves **23.0% → 73.7%** and interval falls **20.3 → 5.1 days**.

> **Loyalty here means frequency and repetition, not basket size.** A "spend $10 more"
> promotion pushes the lever that does not move.

**Segmentation.** K-Means on the three dimensions the brief specifies (order count — log
transformed because it is skewed 2.4 — average basket, reorder rate).

*Stated honestly:* the silhouette score peaks at k = 2 (0.365) and never exceeds 0.37, and
the elbow curve has no sharp break. **This customer base is a continuum, not a set of natural
tribes.** k = 4 was chosen because it separates the two independent levers into segments that
can be acted on differently — a management partition, not a discovery.

| Segment | Customers | % of items | Orders | Basket | Reorder | Interval |
|---|---:|---:|---:|---:|---:|---:|
| **Loyal Regulars** | 44,475 (21.6%) | **53.4%** | 40.6 | 10.1 | **69.0%** | 8.8 d |
| **Big-Basket Stockers** | 33,020 (16.0%) | 20.6% | 10.6 | **19.4** | 46.2% | 16.9 d |
| **Steady Small-Basket** | 62,996 (30.5%) | 17.1% | 12.9 | **7.0** | 49.3% | 15.6 d |
| **Occasional / At-Risk** | 65,718 (31.9%) | 8.9% | 5.7 | 8.0 | **22.3%** | **19.1 d** |

One segment in five buys over half the volume. A third of the customer base produces a
twelfth of it. The two middle segments have nearly the same order count and a 2.8× different
basket — they need opposite interventions.

---

## 7. Product & Category Analysis

**Top products.** Bananas lead with 491,291 units bought by 76,125 customers (**36.9% of all
customers**), then organic bananas (394,930). Nine of the top ten are fresh produce. The
volume leaderboard and the reorder leaderboard are **nearly the same list** — these products
are big because the same people buy them repeatedly, not because many people try them once.

**Highest reorder rate** (minimum 2,000 purchases, because a rate on 12 purchases is noise):
nine of the top ten are **milk variants**, from 86.1% down to 83.9%, with bananas the only
non-dairy entry. These are products people *run out of*, not products they *choose*.

**Concentration.** The top 100 products carry 23.1% of units and the top 1% carry 42.7% — but
reaching 80% of volume still takes **4,548 products**. This is neither a hero-SKU business
nor a flat long tail.

**Volume vs loyalty.** Splitting the 8,563 products with ≥500 purchases at the medians of
that pool (1,287 units, 54.6% reorder rate):

| Quadrant | Products | Units | Share | Example | Strategy |
|---|---:|---:|---:|---|---|
| **Core staples** | 2,537 | 20.4M | **67.5%** | Banana, baby spinach, whole milk | Never out of stock |
| **Traffic drivers** | 1,745 | 6.4M | 21.1% | Olive oil, green onions, ginger | Acquisition, basket fillers |
| **Loyal niche** | 1,746 | 1.4M | 4.7% | Specific cereals, granola bars | Personalised recommendation |
| **Long tail** | 2,535 | 2.0M | 6.6% | Paper plates, speciality cheese | Range completeness |

**Categories.** Produce is 29.2% of units and reaches **74.9% of baskets**; dairy & eggs is
16.7% of units but has the **highest reorder rate of any department, 67.0%**. Together they
are 45.9% of everything sold. At the bottom, personal care (32.2%) and pantry (34.7%) reorder
least.

Most habitual aisle: **milk, 78.2%**. Least: **spices & seasonings, 15.3%**, followed by food
storage (25.5%), cleaning products (29.0%) and baking ingredients (30.5%).

> Every low-reorder category on that list is a **slow-consumption** category. A jar of cumin
> lasts a year. This is cadence, not dissatisfaction.

---

## 8. Reorder Analysis

**59.0%** of all basket lines are reorders; **62.9%** once first orders — which cannot
contain a reorder by definition — are excluded.

**The habit curve.** Reorder rate by the customer's nth order:

| Order # | 1 | 2 | 3 | 4 | 5 | 6 | 10 | 20 | 50 |
|---|---|---|---|---|---|---|---|---|---|
| Reorder rate | 0% | 27.2% | 38.6% | 45.4% | 50.3% | **54.1%** | 63.4% | 73.6% | 81.9% |

The curve gains **27 percentage points between orders 2 and 6** and then flattens. **That is
the habit-formation window**, and it is the most actionable timing finding in the project.

By customer tenure the spread runs from 24.0% (3–4 lifetime orders) to **75.2%** (51–100).
Heavy customers also explore *more* in absolute terms — 169.8 distinct products versus 26.5 —
so repetition and breadth grow together rather than trading off.

**Reorder rate must be benchmarked within its category.** A variance decomposition shows
**aisle explains 56.3%** of the variance in a product's reorder rate and department 40.5%.
The remaining ~44% is where genuine product-level preference lives. An olive oil at 47.7% is
performing well for pantry (mean 32.9%); a milk at 60% is performing badly for dairy
(mean 61.9%).

---

## 9. Market Basket Analysis

**Method.** FP-Growth (a prefix tree rather than Apriori's repeated scans) on a fixed random
sample of **600,000 baskets** (seed 42), at two levels: the **top 300 products** (35.6% of
units; 65.4% of baskets hold ≥2 of them) and **all 134 aisles**. Baskets containing none of
the scoped items stay in the denominator, so support is never inflated by shrinking the universe.

**Thresholds, justified from the data.** Minimum support 0.001 (≥600 of the 600,000 baskets),
minimum confidence 0.05, minimum lift 1.0. At support 0.005 only 95 rules survive and all are
banana pairs; at 0.0005 the output is too rare to merchandise against. Confidence is
deliberately low — with a median basket of 8 items drawn from 49,573 products, a 5%
conditional probability is a strong signal, and the textbook 50% would return only
tautologies. **Lift does the ranking.** Result: **3,048 product rules** and **3,692 aisle
rules** (the brief asks for a minimum of 10).

### The required rule table

| Antecedent | Consequent | Support | Conf. | Lift |
|---|---|---:|---:|---:|
| Total 2% Greek Yogurt Blueberry | Total 2% Strawberry + Total 2% Peach | 0.12% | 18.6% | **75.58** |
| Icelandic Skyr Blueberry | Non Fat Raspberry Yogurt | 0.22% | 38.0% | **75.61** |
| Total 2% Strawberry + Peach | Total 2% Blueberry | 0.12% | 61.6% | 68.12 |
| Sparkling Lemon + Grapefruit Water | Lime Sparkling Water | 0.14% | 47.0% | 32.36 |
| Organic Garlic | Organic Yellow Onion | — | — | **5.64** (pairwise) |
| dry pasta | pasta sauce | 1.95% | 27.4% | **4.41** |
| pasta sauce | dry pasta | 1.95% | 31.4% | **4.41** |
| Limes | Large Lemon | — | — | **4.08** (pairwise) |
| canned meals/beans | canned jarred vegetables | 1.83% | 26.3% | 3.55 |
| Organic Cucumber | Organic Grape Tomatoes | — | — | 3.77 (pairwise) |
| fresh herbs | fresh vegetables | 7.96% | **84.6%** | 1.90 |
| Organic Hass Avocado | Bag of Organic Bananas | 1.94% | 29.1% | 2.45 |

### Business interpretation — three distinct patterns

**Pattern 1 — Flavour variety within one brand (lift 30–76).** The strongest associations in
the dataset are between *different flavours of the same yogurt line* (lift up to 75.6,
confidence up to 61.6%), with sparkling water showing the same shape. **These are not
cross-sell opportunities** — the customer has already chosen the brand and is assembling a
mixed pack inside a decision already made. They are worth something different: *multipack
bundles* (converting four line items into one pick), *range protection* (delisting one
flavour will damage the others), and *substitution logic* (if blueberry is out, the right
substitute is strawberry from the same line, not another brand's blueberry).

**Pattern 2 — Recipe complements (lift 3–6).** These are the genuine cross-sell rules, found
among products that are each individually popular, so rarity cannot explain the association:
garlic↔onion **5.64**, limes↔lemon **4.08**, cucumber↔grape tomatoes **3.77**,
lemon↔avocado 3.62. The customer's intent — *cook a meal* — is only partly expressed by the
first item, which is exactly what makes a prompt useful rather than intrusive.

**Pattern 3 — Category adjacency (high support).** Aisle rules are far more robust, holding
in 1–2% of *all* baskets: **dry pasta ↔ pasta sauce (lift 4.41)**, canned meals ↔ canned
vegetables (3.55), and **fresh herbs → fresh vegetables at 84.6% confidence** — the highest
single-antecedent confidence found at any level. These identify **shopping missions** rather
than product affinities, which makes them the better basis for merchandising, campaign timing
and warehouse pick-path design.

**The negative finding matters commercially.** Bananas are in 14.7% of baskets, so they
co-occur with everything and predict nothing — yet they are the consequent of **21.5% of all
mined rules**. A recommender ranked on confidence would recommend almost nothing else.

### Limitations

1. Association is not causation — garlic and onion co-occur because both are in the recipe.
2. Support is relative to the 600,000-basket sample and the top-300 scope; the *ranking* is
   stable, the absolute support figures are scope-dependent.
3. **No price or margin data exists**, so every bundle recommendation is conditional on a
   margin check.
4. No dates, so seasonality is invisible and would be averaged into the annual figure.

---

## 10. Key Findings

Each stated as **Finding → Evidence → Business meaning**.

**Finding 1 — This is a replenishment business.**
*Evidence:* 59.0% of all 33.8M items sold are reorders (62.9% excluding first orders), rising
to 81.9% by a customer's 50th order.
*Business meaning:* the core product problem is making the known list effortless, not
surfacing novelty. Discovery features compete with the task most customers came to do.

**Finding 2 — The habit forms between orders 2 and 6.**
*Evidence:* reorder rate climbs 27.2% → 54.1% across that window, then flattens (63.4% at
order 10, 81.9% at order 50). By tenure: 24.0% for 3–4 order customers vs 75.2% for 51–100.
*Business meaning:* this is where retention spend has leverage. A customer who reaches their
sixth order is behaving like a retained customer; one who stalls at three is not. After order
10 the spend is largely redundant.

**Finding 3 — Frequency and basket size are independent levers.**
*Evidence:* Spearman ρ = 0.06 between order count and average basket; across order bands the
basket moves 9.6 → 10.4 items while reorder rate moves 23.0% → 73.7%.
*Business meaning:* a single "engagement score" conflates two unrelated behaviours. Steady
Small-Basket customers (7.0 items, 12.9 orders) need basket building; Big-Basket Stockers
(19.4 items, 10.6 orders) need frequency. One campaign cannot do both.

**Finding 4 — Customers run on a weekly clock.**
*Evidence:* 50.9% of repeat orders within 7 days; a spike at exactly day 7 (10.0% vs 7.5% at
day 6, 5.7% at day 8); secondary bumps at 14, 21, 30.
*Business meaning:* the reminder trigger does not have to be invented or A/B-guessed — the
customer base has already chosen it. Deviation from a customer's own established interval is
a better churn signal than any fixed threshold.

**Finding 5 — Produce drives traffic; dairy drives return.**
*Evidence:* produce = 29.2% of units and 74.9% basket penetration, reorder rate 65.1%;
dairy & eggs = 16.7% of units but the highest reorder rate of any department, 67.0%, led by
milk at 78.2%.
*Business meaning:* two different roles justifying two different investments. Produce quality
and availability drive acquisition and basket reach; dairy reliability drives frequency.

**Finding 6 — Reorder rate measures consumption cadence, not satisfaction.**
*Evidence:* aisle explains 56.3% of the variance in product reorder rate (department 40.5%).
The lowest-reordering aisles — spices 15.3%, food storage 25.5%, baking 30.5% — are all
slow-consumption categories.
*Business meaning:* never score a product against the overall 59%. Benchmark within its
category, or every pantry item looks like a failure and every milk looks like a success.

**Finding 7 — The real cross-sell signal is culinary, and the top seller is worthless for it.**
*Evidence:* garlic↔onion lift 5.64, pasta↔pasta sauce 4.41, lime↔lemon 4.08; meanwhile
bananas are in 14.7% of baskets and are the consequent of 21.5% of all rules.
*Business meaning:* recipe-shaped bundles and basket-completion prompts are evidence-backed.
A confidence-ranked recommender is not — it would recommend bananas to everyone.

**Finding 8 — Small orders are a disproportionate operational load.**
*Evidence:* 17.1% of orders contain 3 items or fewer but carry only 3.5% of units; 4.9% are a
single item. These tiny orders have the *highest* reorder rate (65.0%) — they are
forgotten-essentials top-ups.
*Business meaning:* a minimum-order rule would suppress a habit signal. Basket building —
prompting the customer's own usual items at checkout — addresses the economics without
punishing the behaviour.

---

## 11. Business Recommendations

Every recommendation names the evidence it rests on and how it would be measured.

### R1 — Launch replenishment subscriptions, seeded from the milk & yogurt cluster

**Evidence.** The nine highest reorder rates in the catalogue (≥2,000 purchases) are all milk
variants, 83.9–86.1%. Milk is the most habitual aisle at 78.2%; dairy & eggs is the most
habitual department at 67.0%. 50.9% of repeat orders arrive within 7 days.
**Action.** Offer a weekly or fortnightly auto-add for a customer's top 3–5 repeat products,
defaulting to their own observed interval rather than a fixed schedule, with one-tap skip.
**Why it works.** The behaviour already exists at an 84%+ rate; the product is only removing
the retyping. It does not ask the customer to change anything.
**Measure.** Share of orders containing a subscribed item; interval variance before vs after;
churn of subscribers vs a matched control.
**Risk.** Over-delivery damages trust fast. Default to skip-friendly and never auto-add a
slow-consumption category (anything below ~40% reorder rate — pantry, spices, cleaning).

### R2 — Concentrate retention spend on orders 2–6

**Evidence.** Reorder rate climbs 27.2% → 54.1% between orders 2 and 6 and then flattens.
Occasional / At-Risk customers (31.9% of the base, 8.9% of items) average 5.7 orders and a
22.3% reorder rate — they stall exactly in this window.
**Action.** A fixed onboarding sequence over a new customer's first six orders: reorder
prompts from their own first-basket items, a reminder timed to their emerging interval, and
incentives front-loaded to orders 2–4 rather than spread evenly.
**Why it works.** It targets the only part of the lifecycle where the curve is steep. Spend
after order 10 is largely spent on customers who were going to stay.
**Measure.** Share of new customers reaching order 6 within a fixed window; reorder rate at
order 6 vs control.
**Risk.** The dataset has no dates, so "within 90 days" cannot be validated here — the window
needs calibrating against live data before launch.

### R3 — Treat the two middle segments as two different problems

**Evidence.** Order frequency and basket size are uncorrelated (ρ = 0.06). Steady
Small-Basket: 62,996 customers, 7.0 items, 12.9 orders, 15.6-day interval. Big-Basket
Stockers: 33,020 customers, 19.4 items, 10.6 orders, 16.9-day interval.
**Action.** For Small-Basket customers, basket building — complete-your-basket prompts drawn
from the recipe pairs in R4, and a reminder of their own usual items at checkout. For
Stockers, frequency — a replenishment reminder at ~14 days, not a bigger cart.
**Why it works.** Each pushes the lever that is actually movable for that group. A single
"engagement" campaign would push the wrong one for half of them.
**Measure.** Basket size for Small-Basket; order interval for Stockers. Each segment is
judged only on its own metric.
**Risk.** Segments are a partition of a continuum (silhouette ≤ 0.37), so boundaries will
shift on re-run. Assign on current behaviour, re-score regularly, and never expose segment
names to customers.

### R4 — Build basket-completion prompts on recipe pairs, not on popularity

**Evidence.** Among best-selling products: garlic↔onion lift 5.64, lime↔lemon 4.08,
cucumber↔grape tomatoes 3.77, lemon↔avocado 3.62. At aisle level: pasta↔pasta sauce lift
4.41 in 1.95% of baskets. Against this: bananas are the consequent of 21.5% of all rules while
adding no information.
**Action.** Ship three evidenced kits — aromatics (garlic, onion), salad (cucumber, tomatoes,
lemon), pasta night (dry pasta, sauce, parmesan) — and a completion prompt that fires on the
*gap*: garlic in the basket without onion. Explicitly exclude the top ~20 products by basket
penetration from recommendation eligibility.
**Why it works.** It targets intent the first item only partly expresses, which is why the
prompt is useful rather than intrusive. Excluding bananas removes the single largest source
of worthless recommendations.
**Measure.** Prompt acceptance rate, and incremental units of the *consequent* — not total
basket size, which drifts for unrelated reasons.
**Risk.** **No margin data exists in this dataset.** Every bundle must pass a margin check
before launch; a high-lift pair of two low-margin items is commercially worthless.

### R5 — Set service levels by quadrant, and benchmark reorder rate within category

**Evidence.** 2,537 core staples (5% of purchased products) carry 67.5% of units in the
≥500-purchase pool at a 64.8% average reorder rate. Aisle explains 56.3% of the variance in
product reorder rate. Spices reorder at 15.3%, milk at 78.2% — and both are healthy.
**Action.** Tier availability by quadrant: core staples get the highest service-level
guarantee and substitution logic; traffic drivers are managed for breadth; long tail is
reviewed for delisting *only* with a cannibalisation check. Replace the single company-wide
reorder benchmark with a per-aisle one.
**Why it works.** An availability failure on a core staple damages a repeat relationship, not
just one sale. And a single benchmark currently flags every slow-consumption category as
failing when it is behaving normally.
**Measure.** In-stock rate weighted by quadrant; reorder rate tracked as a *deviation from
aisle mean* rather than an absolute.
**Risk.** Flavour-variety products (R4, Pattern 1) are bought as sets — the per-SKU
profitability review that drives delisting will miss that removing one flavour damages the others.

### R6 — Time campaigns to the two differently-shaped weekend peaks

**Evidence.** Days 0 and 1 carry 34.7% of the week, but day 0 peaks 13:00–15:00 with
11.2-item baskets while day 1 peaks 09:00–11:00 with 10.2. 64.9% of orders fall in
09:00–16:00. Evening orders (21:00–23:00) are only 5.3% of volume but carry the largest
baskets (up to 11.0 items).
**Action.** Two separate weekend sends timed to each peak's own shape — a stock-up message
before the day-0 afternoon, a top-up message before the day-1 morning. Schedule
capacity to the hour, not the day: peak-to-trough across days is only 1.41×, across hours it
is 53×.
**Why it works.** A single weekend campaign fires at the wrong time for one of two distinct
shopping occasions.
**Measure.** Open-to-order conversion by send window; basket size by window.
**Risk.** Day names are an assumption — the mapping is undocumented in the source. Validate
against live timestamps before committing spend to a named day.

---

## 12. Conclusion

The brief's closing questions, answered.

**Who are Instacart's customers and how do they shop?** 206,209 customers placing a median of
10 orders of a median 8 items, on a weekly rhythm concentrated in daytime hours. They divide
into a loyal fifth that buys over half the volume, a frequent-but-light group, a
large-basket-but-infrequent group, and a third of the base that never forms the habit.

**Which products and categories matter most?** Produce by reach (29.2% of units, 74.9% of
baskets); dairy by loyalty (67.0% reorder rate). 2,537 core staples carry 67.5% of volume in
the reliable pool. Bananas are the single most important product by every volume measure — and
the least useful one to recommend.

**When do customers buy?** 09:00–16:00 (64.9% of orders), concentrated on two weekend days of
different shapes, on a 7-day repeat clock.

**What is the reorder pattern?** 59.0% of all items. It is built between orders 2 and 6,
compounds to 81.9% by order 50, and is governed far more by how fast a category is consumed
than by how much a product is liked.

**Which products are bought together?** Three different things wearing one name: flavour
variants of a brand (lift up to 75.6 — bundle these), recipe complements (lift 3–6 —
cross-sell these), and category adjacencies (pasta↔sauce, herbs→vegetables — merchandise around these).

**What opportunities follow, and what should the company do?** Six evidence-backed
recommendations in §11, led by replenishment subscriptions seeded from a cluster that already
reorders at 84%+, and by concentrating retention spend on the orders 2–6 window where the
habit curve is actually steep.

**The honest caveat.** This dataset contains no prices, no margins, no dates and no
demographics. Nothing here can be converted into a revenue forecast, nothing can be checked
for seasonality, and every bundle recommendation is conditional on a margin check this data
cannot perform. What it can support — behavioural findings, timing, category structure and
product association — is stated above, and nothing beyond that has been claimed.

---

*Analysis by notebooks 01–06 · dashboard in `dashboard/instacart_dashboard.xlsx` · all
figures in `reports/figures/` · all supporting tables in `reports/tables/`.*
