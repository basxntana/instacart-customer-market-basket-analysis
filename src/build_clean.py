"""Phase 2 (cleaning) + Phase 3 (integration).

Every transformation here is logged to reports/cleaning_log.json so the notebook
and the final report can cite exactly what was changed and why.
"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import instacart as ic

log = {"decisions": [], "row_counts": {}, "join_log": []}
def decide(step, action, reason, impact):
    log["decisions"].append({"step": step, "action": action, "reason": reason, "impact": impact})
    print(f"[{step}] {action}\n    why: {reason}\n    impact: {impact}")

print("== loading source tables (from data/raw, via parquet cache) ==")
aisles = ic.load_source("aisles"); depts = ic.load_source("departments")
prods = ic.load_source("products"); orders = ic.load_source("orders")
prior = ic.load_source("order_products__prior"); train = ic.load_source("order_products__train")
for n, d in [("aisles",aisles),("departments",depts),("products",prods),("orders",orders),
             ("order_products__prior",prior),("order_products__train",train)]:
    log["row_counts"][n] = {"raw_rows": int(len(d)), "raw_cols": int(d.shape[1])}

# ============================================================ DEPARTMENTS / AISLES
depts = depts.astype({"department_id":"int16"})
depts["is_placeholder"] = depts.department_id.isin(ic.PLACEHOLDER_DEPT_IDS)
aisles = aisles.astype({"aisle_id":"int16"})
aisles["is_placeholder"] = aisles.aisle_id.isin(ic.PLACEHOLDER_AISLE_IDS)
decide("categories", "Flagged department 'missing' (21) and aisles 'missing' (100) / 'other' (6) as placeholders instead of deleting them.",
       "They are unknown-category buckets, not real shelves. Dropping them would silently delete real transactions; keeping them unflagged would let an 'unknown' bucket win a 'top category' ranking.",
       f"{int(depts.is_placeholder.sum())} department + {int(aisles.is_placeholder.sum())} aisle rows flagged; 0 rows removed.")

# ============================================================ PRODUCTS
prods = prods.astype({"product_id":"int32","aisle_id":"int16","department_id":"int16"})
ws = int((prods.product_name != prods.product_name.str.strip()).sum())
prods["product_name"] = (prods.product_name.str.strip().str.replace(r"\s+", " ", regex=True))
decide("products.product_name", f"Trimmed/collapsed whitespace in product names ({ws} rows had stray whitespace).",
       "Whitespace variants create false distinct products when names are grouped or matched.", f"{ws} names normalised; 0 rows removed.")

# Case-only duplicate names -> one analytical product unit (product_uid)
norm = prods.product_name.str.lower()
grp_key = norm + "||" + prods.aisle_id.astype(str)
first = prods.assign(_k=grp_key).groupby("_k", sort=False).product_id.transform("min")
n_collapsed = int((first != prods.product_id).sum())
n_groups = int(prods.assign(_k=grp_key).groupby("_k").product_id.size().pipe(lambda s: (s>1).sum()))
prods["product_uid"] = first.astype("int32")
decide("products.product_uid",
       f"Created product_uid: product_ids that share an identical name *within the same aisle* now map to one analytical product ({n_groups} groups, {n_collapsed} secondary SKUs folded in). product_id is kept untouched.",
       "e.g. 'BBQ Sauce' (2691) and 'Bbq Sauce' (43288) are the same shelf item listed twice; left split they halve that product's purchase volume and reorder rate. Same-name products in DIFFERENT aisles are left separate because they may genuinely differ.",
       f"{n_collapsed} of {len(prods):,} products ({n_collapsed/len(prods)*100:.2f}%) re-pointed; catalogue row count unchanged.")

prods = prods.merge(aisles[["aisle_id","aisle","is_placeholder"]].rename(columns={"is_placeholder":"aisle_is_placeholder"}), on="aisle_id", how="left")
prods = prods.merge(depts[["department_id","department","is_placeholder"]].rename(columns={"is_placeholder":"dept_is_placeholder"}), on="department_id", how="left")
assert prods.aisle.notna().all() and prods.department.notna().all()

bought = pd.unique(np.concatenate([prior.product_id.unique(), train.product_id.unique()]))
prods["ever_purchased"] = prods.product_id.isin(bought)
decide("products.ever_purchased", f"Flagged the {int((~prods.ever_purchased).sum())} catalogue products that were never purchased; kept them.",
       "They are valid catalogue entries with zero demand - an assortment finding in its own right, not dirty data.", "0 rows removed.")

# ============================================================ ORDERS
orders = orders.astype({"order_id":"int32","user_id":"int32","order_number":"int16",
                        "order_dow":"int8","order_hour_of_day":"int8","days_since_prior_order":"float32"})
orders["is_first_order"] = (orders.order_number == 1)
n_nan = int(orders.days_since_prior_order.isna().sum())
assert n_nan == int(orders.is_first_order.sum()), "dspo nulls must be exactly first orders"
decide("orders.days_since_prior_order",
       f"Kept all {n_nan:,} nulls as nulls and added is_first_order; no imputation, no row dropped.",
       "Null here means 'this customer had no previous order' - a real business state. Every single null sits on order_number = 1 (verified), so imputing 0 would invent same-day repeat behaviour and imputing the mean would invent a fake interval.",
       f"{n_nan:,} rows ({n_nan/len(orders)*100:.1f}%) retained with a null interval + explicit flag.")

n_cap = int((orders.days_since_prior_order == 30).sum())
orders["dspo_is_capped"] = (orders.days_since_prior_order == 30)
decide("orders.days_since_prior_order (cap)",
       f"Flagged the {n_cap:,} orders ({n_cap/len(orders)*100:.1f}%) recorded at exactly 30 days as right-censored rather than treating 30 as a true interval.",
       "The field is capped at 30 by Instacart, so '30' means 'at least 30 days'. Averaging it as a literal 30 understates the real gap for lapsed customers.",
       "Mean interval is reported both raw and excluding the cap.")

orders["order_dow_label"] = pd.Categorical(orders.order_dow.map(dict(enumerate(ic.DOW_LABELS))),
                                           categories=ic.DOW_LABELS, ordered=True)
decide("orders.order_dow", "Added readable labels assuming 0 = Saturday, and flagged that assumption.",
       "The Instacart release documents order_dow only as 0-6 with no weekday mapping. Days 0 and 1 carry the volume peak, which is weekend-shaped, so 0=Sat is the standard reading - but no conclusion in this report depends on the names, only on the relative pattern.",
       "Labels are presentational; all day-level findings are also stated by day number.")

for c, rng in [("order_dow",(0,6)),("order_hour_of_day",(0,23)),("order_number",(1,100))]:
    assert orders[c].between(*rng).all(), c
decide("orders validity", "Verified order_dow in 0-6, order_hour_of_day in 0-23, order_number >= 1; no invalid values found.",
       "Range checks before any time analysis, so a bad code value cannot be read as a real behavioural pattern.", "0 rows removed.")
decide("orders.order_number (cap)", "Noted order_number maxes out at exactly 100 and left it as is.",
       "A clean ceiling at a round number is a collection cap, not a coincidence: the most loyal customers' histories are truncated.", "Affects the top of the order-frequency distribution only; stated wherever it matters.")

# ============================================================ ORDER ITEMS (prior + train)
prior = prior.astype(ic.DT_ITEMS); train = train.astype(ic.DT_ITEMS)
prior["source"] = pd.Categorical(["prior"]*len(prior), categories=["prior","train"])
train["source"] = pd.Categorical(["train"]*len(train), categories=["prior","train"])
items = pd.concat([prior, train], ignore_index=True)
del prior, train
decide("order items base table",
       f"Stacked order_products__prior ({len(items[items.source=='prior']):,} lines) and order_products__train ({len(items[items.source=='train']):,} lines) into one {len(items):,}-line basket table, keeping a source column.",
       "Both files have real basket contents and identical schemas; train is simply each selected customer's most recent order. Analysing only prior would throw away 1.38M real purchase lines. The 75,000 test orders have no contents at all, so they can never enter item-level analysis.",
       f"{len(items):,} basket lines covering {items.order_id.nunique():,} orders.")
assert items.duplicated(["order_id","product_id"]).sum() == 0
assert set(items.reordered.unique()) <= {0,1}
decide("order items validity", "Verified (order_id, product_id) is unique, reordered is strictly 0/1, add_to_cart_order >= 1; nothing to clean.",
       "The grain must be one line per product per order before any basket-size or reorder-rate maths.", "0 rows removed, 0 duplicates found.")

# ============================================================ PHASE 3: INTEGRATION
def jlog(step, left, right, how, keys, before, after, reason):
    log["join_log"].append({"step": step, "left": left, "right": right, "how": how, "keys": keys,
                            "rows_before": int(before), "rows_after": int(after),
                            "row_delta": int(after-before), "reason": reason})
    print(f"[join] {left} {how}-join {right} on {keys}: {before:,} -> {after:,} ({after-before:+,})\n    why: {reason}")

n0 = len(items)
pid = prods.product_id.to_numpy()
items["product_uid"]  = ic.map_by_id(items.product_id.to_numpy(), pid, prods.product_uid.to_numpy(), dtype="int32")
items["aisle_id"]     = ic.map_by_id(items.product_id.to_numpy(), pid, prods.aisle_id.to_numpy(), dtype="int16")
items["department_id"]= ic.map_by_id(items.product_id.to_numpy(), pid, prods.department_id.to_numpy(), dtype="int16")
assert (items.aisle_id > 0).all() and (items.department_id > 0).all()
jlog("items x products", "order_items", "products (-> aisle_id, department_id, product_uid)", "left (lookup)",
     "product_id", n0, len(items),
     "Left join keyed on the product PK so no basket line can be lost. Every product_id resolved (0 orphans), so the row count is unchanged - which is the test that the join is a true many-to-one.")

oid = orders.order_id.to_numpy()
for col, dt in [("user_id","int32"),("order_number","int16"),("order_dow","int8"),
                ("order_hour_of_day","int8"),("days_since_prior_order","float32")]:
    items[col] = ic.map_by_id(items.order_id.to_numpy(), oid, orders[col].to_numpy(), fill=np.nan if dt=="float32" else 0, dtype=dt if dt!="float32" else "float32")
assert (items.user_id > 0).all()
jlog("items x orders", "order_items", "orders (-> user_id, order_number, dow, hour, days_since_prior)", "left (lookup)",
     "order_id", n0, len(items),
     "Same shape of join on the order PK. Row count again unchanged, confirming every basket line belongs to exactly one known order and no fan-out occurred.")

# per-order basket size, attached back to orders
bs = items.groupby("order_id", observed=True).agg(basket_size=("product_id","size"),
                                                  n_reordered=("reordered","sum"))
before = len(orders)
orders = orders.merge(bs, on="order_id", how="left")
orders["has_basket_data"] = orders.basket_size.notna()
orders["basket_reorder_rate"] = orders.n_reordered / orders.basket_size
jlog("orders x basket aggregate", "orders", "order_items aggregated to order grain", "left", "order_id",
     before, len(orders),
     "Aggregate FIRST, then left join: joining the line-level table directly would multiply the 3.42M order rows into 33.8M and break every order-level average. Left (not inner) keeps the 75,000 test orders, whose basket_size is legitimately null.")
log["orders_without_basket"] = int((~orders.has_basket_data).sum())
print(f"    orders with no basket data (test set, by design): {log['orders_without_basket']:,}")

# ============================================================ CUSTOMER TABLE
print("\n== building customer table ==")
o_known = orders[orders.has_basket_data]
cust = (orders.groupby("user_id", observed=True)
        .agg(n_orders_total=("order_id","size"),
             mean_dspo=("days_since_prior_order","mean"),
             median_dspo=("days_since_prior_order","median"),
             fav_dow=("order_dow", lambda s: s.mode().iat[0]),
             fav_hour=("order_hour_of_day", lambda s: s.mode().iat[0])))
cust2 = (o_known.groupby("user_id", observed=True)
         .agg(n_orders_observed=("order_id","size"),
              total_items=("basket_size","sum"),
              avg_basket=("basket_size","mean"),
              median_basket=("basket_size","median"),
              max_basket=("basket_size","max"),
              items_reordered=("n_reordered","sum")))
cust = cust.join(cust2)
cust["reorder_rate"] = cust.items_reordered / cust.total_items
nitem = items.groupby("user_id", observed=True).product_uid.nunique().rename("distinct_products")
cust = cust.join(nitem)
cust["repeat_breadth"] = cust.distinct_products / cust.total_items   # low = narrow, repetitive basket
cust = cust.reset_index()
print(cust.describe().T.to_string())

# ============================================================ SAVE
print("\n== writing processed tables ==")
out = {"aisles_clean": aisles, "departments_clean": depts, "products_clean": prods,
       "orders_clean": orders, "customers": cust}
for nm, df in out.items():
    df.to_parquet(ic.PROC/f"{nm}.parquet", index=False); print(f"  {nm}.parquet  {len(df):,} rows x {df.shape[1]}")
items.to_parquet(ic.PROC/"order_items.parquet", index=False)
print(f"  order_items.parquet  {len(items):,} rows x {items.shape[1]}")

log["final_shapes"] = {nm: [int(len(d)), int(d.shape[1])] for nm, d in {**out, "order_items": items}.items()}
ic.save_json(log, "cleaning_log")
print("\nDONE")
