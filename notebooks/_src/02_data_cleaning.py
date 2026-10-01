# %% [markdown]
# # 02 · Data Cleaning & Integration
#
# **Phases 2 and 3 of the brief.**
#
# The governing rule from the brief: *do not delete data just because it looks unusual;
# every cleaning action must have a defensible reason.* Notebook 01 found that this dataset
# is structurally clean — no orphan keys, no duplicate rows, no invalid codes. So this
# notebook deletes **zero rows**. What it does instead is make four pieces of meaning
# explicit that are currently hidden in the raw values, and then integrate the six tables
# into an analysis-ready model.
#
# The executable version of everything below is `src/build_clean.py`; it is run at the end
# of this notebook so the processed files on disk are always the ones this notebook argues for.

# %%
import sys, pathlib, warnings, subprocess
sys.path.insert(0, str(pathlib.Path.cwd().parent / "src"))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import instacart as ic
plt = ic.set_style()
pd.set_option("display.width", 170, "display.max_columns", 40, "display.max_colwidth", 90)

aisles, depts = ic.load_source("aisles"), ic.load_source("departments")
prods, orders = ic.load_source("products"), ic.load_source("orders")
print(f"raw products {len(prods):,} | raw orders {len(orders):,}")

# %% [markdown]
# ## 2.1 Decision 1 — `days_since_prior_order` nulls stay null
#
# 206,209 nulls. The brief names this case explicitly. The question is not *"how do we fill
# it?"* but *"what does it mean?"*.

# %%
chk = pd.DataFrame({
    "nulls in days_since_prior_order": [int(orders.days_since_prior_order.isna().sum())],
    "orders with order_number = 1":    [int((orders.order_number==1).sum())],
    "distinct customers":              [int(orders.user_id.nunique())],
    "nulls NOT on a first order":      [int((orders.days_since_prior_order.isna() & (orders.order_number!=1)).sum())],
}).T.rename(columns={0:"count"})
display(chk)

# %% [markdown]
# All three counts are identical and the fourth is zero. The null is not a gap in collection —
# it is the statement *"this customer had no previous order"*. Three options and why two lose:
#
# | option | consequence |
# |---|---|
# | drop the rows | deletes every customer's first order — 6% of all orders, and the entire acquisition picture |
# | impute 0 | invents 206,209 same-day repeat purchases that never happened; inflates the "orders within 3 days" figure |
# | **keep null + flag** | the interval analysis simply excludes orders that have no interval, which is correct |
#
# **Action: keep the null, add `is_first_order`.** Rows removed: 0.

# %%
orders["is_first_order"] = orders.order_number == 1
print(f"is_first_order = True on {orders.is_first_order.sum():,} rows ({orders.is_first_order.mean()*100:.1f}%)")

# %% [markdown]
# ## 2.2 Decision 2 — the 30-day cap is flagged, not averaged away
#
# Notebook 01 showed a 20x cliff between 29 and 30 days. The field is right-censored: "30"
# means "30 or more". That single fact changes the headline retention number.

# %%
d = orders.days_since_prior_order
comp = pd.DataFrame({
    "metric": ["mean interval (raw, 30 treated as a real value)",
               "mean interval (excluding the censored 30s)",
               "median interval (raw)", "share of orders at the cap"],
    "value": [d.mean(), d[d<30].mean(), d.median(), (d==30).mean()*100],
})
display(comp.round(2))
print("Reporting the raw mean alone would claim the average customer returns every ~11.1 days.")
print("Excluding the censored values, customers who DO come back return every ~8.7 days, and")
print("separately 10.8% of orders follow a gap of a month or more. Those are two different")
print("business stories and the raw mean hides both.")

# %%
orders["dspo_is_capped"] = orders.days_since_prior_order == 30
print(f"dspo_is_capped = True on {orders.dspo_is_capped.sum():,} rows")

# %% [markdown]
# **Action: add `dspo_is_capped`; report the interval both ways everywhere.** Rows removed: 0.

# %% [markdown]
# ## 2.3 Decision 3 — duplicate product identities get one analytical id
#
# This is the only change that alters an analytical result, so it gets the most scrutiny.

# %%
prods["product_name"] = prods.product_name.str.strip().str.replace(r"\s+", " ", regex=True)
norm = prods.product_name.str.lower()
grp = norm + "||" + prods.aisle_id.astype(str)
sizes = grp.value_counts()
dups = prods.assign(_k=grp)[grp.isin(sizes[sizes>1].index)].sort_values("_k")
print(f"{sizes[sizes>1].size} groups of products share an identical name within the same aisle")
display(dups[["product_id","product_name","aisle_id","department_id"]].head(8))

# %%
# What it costs to leave them split: measure one group end to end.
items_s = ic.load_source("order_products__prior")[["product_id","reordered"]]
ex = dups[dups.product_name.str.lower()=="bbq sauce"]
if len(ex) < 2:
    ex = dups.groupby("_k").filter(lambda g: len(g)==2).head(2)
ids = ex.product_id.tolist()
sub = items_s[items_s.product_id.isin(ids)]
split = sub.groupby("product_id").agg(purchases=("reordered","size"), reorders=("reordered","sum"))
split["reorder_rate"] = split.reorders/split.purchases
merged = pd.DataFrame({"purchases":[split.purchases.sum()], "reorders":[split.reorders.sum()]},
                      index=[f"merged ({' + '.join(map(str, ids))})"])
merged["reorder_rate"] = merged.reorders/merged.purchases
print(f"Worked example — '{ex.product_name.iloc[0]}' listed under {len(ids)} product_ids:")
display(pd.concat([split, merged]))
rank_split = (items_s.product_id.value_counts().rank(ascending=False, method="min").loc[ids].min())
tot = items_s.product_id.value_counts()
tot_merged = tot.copy(); tot_merged.loc[ids[0]] = tot.loc[ids].sum()
tot_merged = tot_merged.drop(ids[1:])
rank_merged = tot_merged.rank(ascending=False, method="min").loc[ids[0]]
print(f"Best rank while split: #{rank_split:,.0f}   Rank once merged: #{rank_merged:,.0f}")

# %% [markdown]
# Splitting one shelf item across two ids does not just lose volume — it moves the product
# down the ranking, which is exactly the table a merchandiser would act on.
#
# The rule is deliberately conservative: **merge only when the name is identical *and* the
# aisle is identical.** 19 of the 99 name-groups span different aisles (e.g. a name reused
# across two categories) and those stay separate, because a shared name is not proof of a
# shared product. `product_id` is never overwritten — a new column `product_uid` is added
# beside it, so the raw grain is always recoverable.

# %%
prods["product_uid"] = prods.assign(_k=grp).groupby("_k", sort=False).product_id.transform("min")
n_folded = int((prods.product_uid != prods.product_id).sum())
print(f"Action: product_uid added. {n_folded} of {len(prods):,} products ({n_folded/len(prods)*100:.2f}%) "
      f"now point at a sibling id. Catalogue rows removed: 0.")

# %% [markdown]
# ## 2.4 Decision 4 — placeholder categories are flagged, never ranked

# %%
depts["is_placeholder"] = depts.department_id.isin(ic.PLACEHOLDER_DEPT_IDS)
aisles["is_placeholder"] = aisles.aisle_id.isin(ic.PLACEHOLDER_AISLE_IDS)
display(pd.concat([
    depts[depts.is_placeholder].assign(level="department").rename(columns={"department":"name","department_id":"id"})[["level","id","name"]],
    aisles[aisles.is_placeholder].assign(level="aisle").rename(columns={"aisle":"name","aisle_id":"id"})[["level","id","name"]],
]))
print("Kept in all totals (they are real purchases), excluded from every 'top category' ranking.")
print("Note aisle 108 'other creams cheeses' is a genuine shelf and is NOT flagged — the word")
print("'other' in a name is not sufficient evidence.")

# %% [markdown]
# ## 2.5 Outliers — examined, and kept
#
# The brief asks for "relevant outliers". The honest finding is that there are none that
# warrant removal. An outlier is only a problem if it is *impossible* or if it is *not the
# thing you are measuring*. Neither applies here.

# %%
basket = ic.load_source("order_products__prior")[["order_id"]].groupby("order_id").size()
tails = pd.DataFrame({
    "statistic": ["p99 basket size","max basket size","orders above p99","max orders per customer",
                  "customers at the 100-order cap","single-item orders"],
    "value": [basket.quantile(.99), basket.max(), int((basket>basket.quantile(.99)).sum()),
              int(orders.groupby('user_id').size().max()), int((orders.order_number==100).sum()),
              int((basket==1).sum())],
})
display(tails)
print("\nA 145-item grocery order is a monthly stock-up, not a data error. A 100-order customer")
print("is the dataset's collection ceiling, not an anomaly. Removing either would delete exactly")
print("the high-value behaviour this project is supposed to explain. Kept — and the capped")
print("values are flagged so no average silently depends on them.")

# %% [markdown]
# ## 2.6 What was *not* done, and why
#
# | candidate action | verdict |
# |---|---|
# | drop rows with nulls | **no** — the only nulls carry meaning (§2.1) |
# | de-duplicate rows | **no** — there are zero exact duplicates; the key `(order_id, product_id)` is already unique |
# | fix data types | **done at load**, not as a repair — explicit dtypes for memory, not because anything was wrong |
# | remove invalid categories | **no** — every FK resolves; placeholders are flagged, not deleted |
# | trim outliers | **no** — all extremes are plausible grocery behaviour (§2.5) |
# | drop the `test` orders | **no** — they have no basket contents, but their timing fields are valid and used in the time analysis |
# | drop never-purchased products | **no** — zero demand on a live SKU is an assortment finding |

# %% [markdown]
# ## 2.7 Phase 3 — Data Integration
#
# The required chain is Customer → Order → Order Product → Product → Aisle → Department.
#
# One join decision drives everything: **aggregate before joining, never after.** The fact
# table has 33.8M lines and `orders` has 3.42M rows. Joining lines onto orders directly
# would fan `orders` out to 33.8M rows, and every order-level average computed afterwards —
# basket size, orders per hour, interval — would be weighted by basket size instead of
# counting orders. So basket size is aggregated to order grain first, then joined back.
#
# The row count before and after each join is the test: for a many-to-one join on a primary
# key, the row count must not change. If it does, the join is wrong.

# %%
print("Running the full pipeline (src/build_clean.py) — cleaning + integration + customer table.\n")
r = subprocess.run([sys.executable, "../src/build_clean.py"], capture_output=True, text=True)
print(r.stdout[-7000:])
if r.returncode: print("STDERR:", r.stderr[-3000:])

# %% [markdown]
# ### Join log

# %%
log = ic.load_json("cleaning_log")
jl = pd.DataFrame(log["join_log"])
display(jl[["left","right","how","keys","rows_before","rows_after","row_delta"]])
for j in log["join_log"]:
    print(f"\n• {j['left']} ⋈ {j['right']}\n  {j['reason']}")

# %% [markdown]
# **Impact on record count: zero, on every join.** That is the result we wanted and the
# reason the checks are shown. Every basket line found its product and its order; no line
# was duplicated by a one-to-many fan-out; the 75,000 test orders survive the left join with
# a null basket size rather than disappearing through an inner join.

# %% [markdown]
# ### Cleaning log — the complete audit trail

# %%
dl = pd.DataFrame(log["decisions"])
ic.savetable(dl, "cleaning_decisions")
for i, d in enumerate(log["decisions"], 1):
    print(f"\n[{i}] {d['step']}\n    action: {d['action']}\n    why:    {d['reason']}\n    impact: {d['impact']}")

# %% [markdown]
# ## 2.8 The analysis-ready model

# %%
shapes = pd.DataFrame([{"table": k, "rows": v[0], "columns": v[1]} for k, v in log["final_shapes"].items()])
display(shapes)

# %%
oc = ic.load_clean("orders_clean")
cu = ic.load_clean("customers")
it = ic.load_clean("order_items", columns=["order_id","user_id","product_uid","aisle_id","department_id","reordered"])
print("order_items (the fact table) — one row per product per order:")
display(it.head(5))
print("\norders_clean — one row per order:")
display(oc.head(3))
print("\ncustomers — one row per customer, fully derived (there is no users table in the source):")
display(cu.head(3))

# %%
# Final integrity assertions: the data model has to hold before any analysis is run on it.
checks = [
 ("every basket line resolves to a product", bool((it.product_uid>0).all())),
 ("every basket line resolves to an aisle", bool((it.aisle_id>0).all())),
 ("every basket line resolves to a department", bool((it.department_id>0).all())),
 ("every basket line resolves to a customer", bool((it.user_id>0).all())),
 ("order_items row count unchanged by integration", len(it)==33_819_106),
 ("orders_clean row count unchanged", len(oc)==3_421_083),
 ("one row per customer", cu.user_id.is_unique),
 ("customer count matches orders", cu.user_id.nunique()==oc.user_id.nunique()),
 ("only test orders lack basket data", int((~oc.has_basket_data).sum())==75_000),
 ("items total reconciles with per-order basket sizes", int(oc.basket_size.sum())==len(it)),
]
display(pd.DataFrame(checks, columns=["assertion","passes"]))
assert all(c[1] for c in checks), "integration integrity failed"
print("\nAll integration assertions pass. Phases 2 and 3 complete — 0 rows deleted, 0 values imputed.")
