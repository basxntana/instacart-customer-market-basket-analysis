"""Analysis functions for Phases 4-9. Pure: each returns a DataFrame/dict, no printing,
so the notebooks can display them and the report can cite them from one implementation."""
from __future__ import annotations
import numpy as np, pandas as pd

# ------------------------------------------------------------------ Phase 4: KPI
def overall_kpis(orders, items, products, customers) -> pd.DataFrame:
    known = orders[orders.has_basket_data]
    first_excl = items[items.order_number > 1]
    rows = [
        ("Total customers", customers.user_id.nunique(), "distinct user_id in orders"),
        ("Total orders (all)", len(orders), "every order row, incl. 75,000 test orders with no contents"),
        ("Total orders (with basket contents)", len(known), "prior + train; the base for all item-level analysis"),
        ("Total items purchased", len(items), "basket lines = product x order"),
        ("Products in catalogue", len(products), "products.csv rows"),
        ("Products ever purchased", items.product_uid.nunique(), "distinct analytical products with >=1 purchase"),
        ("Average basket size", known.basket_size.mean(), "items per order"),
        ("Median basket size", known.basket_size.median(), "items per order"),
        ("Average orders per customer", len(orders)/customers.user_id.nunique(), "all orders / customers"),
        ("Median orders per customer", customers.n_orders_total.median(), "per-customer order count"),
        ("Reorder rate (all items)", items.reordered.mean()*100, "% of basket lines flagged as a reorder"),
        ("Reorder rate (excl. first orders)", first_excl.reordered.mean()*100, "first orders cannot contain reorders by definition"),
        ("Average days between orders", orders.days_since_prior_order.mean(), "raw, incl. the 30-day cap"),
        ("Average days between orders (excl. 30-day cap)", orders.loc[~orders.dspo_is_capped, "days_since_prior_order"].mean(), "excludes right-censored values"),
    ]
    return pd.DataFrame(rows, columns=["kpi", "value", "definition"])

def product_kpis(items, products, min_purchases=100) -> pd.DataFrame:
    """One row per analytical product (product_uid)."""
    g = items.groupby("product_uid", observed=True).agg(
        purchases=("reordered", "size"),
        reorders=("reordered", "sum"),
        n_orders=("order_id", "nunique"),
        n_customers=("user_id", "nunique"),
        mean_cart_position=("add_to_cart_order", "mean"))
    g["reorder_rate"] = g.reorders / g.purchases
    g["purchases_per_customer"] = g.purchases / g.n_customers
    meta = (products.loc[products.product_id == products.product_uid,
                         ["product_uid", "product_name", "aisle", "department",
                          "aisle_is_placeholder", "dept_is_placeholder"]])
    g = g.reset_index().merge(meta, on="product_uid", how="left")
    g["volume_share"] = g.purchases / g.purchases.sum()
    g["is_reliable"] = g.purchases >= min_purchases   # reorder rate is noise on tiny samples
    return g.sort_values("purchases", ascending=False).reset_index(drop=True)

def category_kpis(items, lookup, level="department") -> pd.DataFrame:
    key = f"{level}_id"
    g = items.groupby(key, observed=True).agg(
        units=("reordered", "size"), reorders=("reordered", "sum"),
        n_orders=("order_id", "nunique"), n_customers=("user_id", "nunique"),
        n_products=("product_uid", "nunique"))
    g["reorder_rate"] = g.reorders / g.units
    g["units_share"] = g.units / g.units.sum()
    g["basket_penetration"] = g.n_orders / g.n_orders.max() if level else np.nan
    g = g.reset_index().merge(lookup, on=key, how="left")
    return g.sort_values("units", ascending=False).reset_index(drop=True)

def category_penetration(items, orders, level="department") -> pd.Series:
    """Share of baskets that contain at least one item from the category."""
    n_baskets = items.order_id.nunique()
    return (items.groupby(f"{level}_id", observed=True).order_id.nunique() / n_baskets).rename("basket_penetration")

# ------------------------------------------------------------------ Phase 5: customer
def order_frequency_dist(customers, bins=(0,4,6,10,20,50,101)) -> pd.DataFrame:
    labels = ["3-4 orders","5-6","7-10","11-20","21-50","51-100"]
    b = pd.cut(customers.n_orders_total, bins=list(bins), labels=labels, right=True)
    out = (customers.assign(bucket=b).groupby("bucket", observed=True)
           .agg(customers=("user_id","size"), avg_basket=("avg_basket","mean"),
                reorder_rate=("reorder_rate","mean"), total_items=("total_items","sum")))
    out["customer_share"] = out.customers / out.customers.sum()
    out["item_share"] = out.total_items / out.total_items.sum()
    return out.reset_index()

def basket_size_dist(orders, bins=(0,3,5,10,15,20,30,50,150)) -> pd.DataFrame:
    labels = ["1-3","4-5","6-10","11-15","16-20","21-30","31-50","51+"]
    known = orders[orders.has_basket_data]
    b = pd.cut(known.basket_size, bins=list(bins), labels=labels, right=True)
    out = (known.assign(bucket=b).groupby("bucket", observed=True)
           .agg(orders=("order_id","size"), items=("basket_size","sum"),
                reorder_rate=("basket_reorder_rate","mean")))
    out["order_share"] = out["orders"]/out["orders"].sum()
    out["item_share"] = out["items"]/out["items"].sum()
    return out.reset_index()

SEG_FEATURES = ["n_orders_observed", "avg_basket", "reorder_rate"]

def segment_customers(customers, k=4, seed=42, features=SEG_FEATURES):
    """K-Means on the three dimensions the brief asks for, on log-scaled order count
    (order count is heavily right-skewed; untransformed it would dominate the distance)."""
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    X = customers[features].copy()
    X["n_orders_observed"] = np.log1p(X.n_orders_observed)
    Xs = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(Xs)
    return km.labels_, Xs, km

def segment_scan(customers, ks=range(2, 8), seed=42, sample=40000):
    """Elbow (inertia) + silhouette, so k is chosen with evidence, not by taste."""
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    X = customers[SEG_FEATURES].copy(); X["n_orders_observed"] = np.log1p(X.n_orders_observed)
    Xs = StandardScaler().fit_transform(X)
    rng = np.random.default_rng(seed); idx = rng.choice(len(Xs), min(sample, len(Xs)), replace=False)
    rows = []
    for k in ks:
        km = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(Xs)
        rows.append({"k": k, "inertia": km.inertia_,
                     "silhouette": silhouette_score(Xs[idx], km.labels_[idx])})
    return pd.DataFrame(rows)

def segment_profile(customers, label_col="segment") -> pd.DataFrame:
    p = (customers.groupby(label_col, observed=True)
         .agg(customers=("user_id","size"), avg_orders=("n_orders_observed","mean"),
              med_orders=("n_orders_observed","median"), avg_basket=("avg_basket","mean"),
              reorder_rate=("reorder_rate","mean"), avg_interval=("mean_dspo","mean"),
              distinct_products=("distinct_products","mean"), total_items=("total_items","sum")))
    p["customer_share"] = p.customers/p.customers.sum()
    p["item_share"] = p.total_items/p.total_items.sum()
    p["items_per_customer"] = p.total_items/p.customers
    return p.reset_index()

# ------------------------------------------------------------------ Phase 6: time
def by_hour(orders, items=None) -> pd.DataFrame:
    g = orders.groupby("order_hour_of_day", observed=True).agg(orders=("order_id","size"))
    g["order_share"] = g.orders/g.orders.sum()
    known = orders[orders.has_basket_data].groupby("order_hour_of_day", observed=True)
    g["avg_basket"] = known.basket_size.mean()
    g["reorder_rate"] = known.n_reordered.sum()/known.basket_size.sum()
    return g.reset_index()

def by_dow(orders) -> pd.DataFrame:
    g = orders.groupby("order_dow", observed=True).agg(orders=("order_id","size"))
    g["order_share"] = g.orders/g.orders.sum()
    known = orders[orders.has_basket_data].groupby("order_dow", observed=True)
    g["avg_basket"] = known.basket_size.mean()
    g["reorder_rate"] = known.n_reordered.sum()/known.basket_size.sum()
    return g.reset_index()

def dow_hour_matrix(orders) -> pd.DataFrame:
    return (orders.pivot_table(index="order_dow", columns="order_hour_of_day",
                               values="order_id", aggfunc="size").fillna(0))

def by_dspo(orders) -> pd.DataFrame:
    known = orders[orders.has_basket_data & orders.days_since_prior_order.notna()]
    g = known.groupby("days_since_prior_order", observed=True).agg(
        orders=("order_id","size"), avg_basket=("basket_size","mean"),
        items=("basket_size","sum"), reorders=("n_reordered","sum"))
    g["reorder_rate"] = g["reorders"]/g["items"]
    g["order_share"] = g["orders"]/g["orders"].sum()
    return g.reset_index()

# ------------------------------------------------------------------ Phase 9: reorder
def reorder_by_order_number(items, cap=50) -> pd.DataFrame:
    s = items[items.order_number <= cap]
    g = s.groupby("order_number", observed=True).agg(
        items=("reordered","size"), reorders=("reordered","sum"), orders=("order_id","nunique"))
    g["reorder_rate"] = g.reorders/g["items"]
    g["avg_basket"] = g["items"]/g.orders
    return g.reset_index()

def reorder_by_customer_tenure(items, customers) -> pd.DataFrame:
    labels = ["3-4 orders","5-6","7-10","11-20","21-50","51-100"]
    b = pd.cut(customers.n_orders_total, [0,4,6,10,20,50,101], labels=labels)
    m = dict(zip(customers.user_id, b))
    bb = items.user_id.map(m)
    g = items.assign(bucket=bb).groupby("bucket", observed=True).agg(
        items=("reordered","size"), reorders=("reordered","sum"),
        customers=("user_id","nunique"), distinct_products=("product_uid","nunique"))
    g["reorder_rate"] = g.reorders/g["items"]
    return g.reset_index()

def reorder_by_cart_position(items, cap=25) -> pd.DataFrame:
    s = items[items.add_to_cart_order <= cap]
    g = s.groupby("add_to_cart_order", observed=True).agg(
        items=("reordered","size"), reorders=("reordered","sum"))
    g["reorder_rate"] = g.reorders/g["items"]
    return g.reset_index()

def volume_vs_reorder_quadrants(pk, min_purchases=500) -> pd.DataFrame:
    """Split reliable products into the four volume x loyalty quadrants the brief asks for."""
    d = pk[pk.purchases >= min_purchases].copy()
    vmed, rmed = d.purchases.median(), d.reorder_rate.median()
    d["quadrant"] = np.select(
        [(d.purchases >= vmed) & (d.reorder_rate >= rmed),
         (d.purchases >= vmed) & (d.reorder_rate < rmed),
         (d.purchases < vmed) & (d.reorder_rate >= rmed)],
        ["Core staples (high volume + high loyalty)", "Traffic drivers (high volume, low loyalty)",
         "Loyal niche (low volume, high loyalty)"], default="Long tail (low volume, low loyalty)")
    d.attrs["volume_median"] = vmed; d.attrs["reorder_median"] = rmed
    return d
