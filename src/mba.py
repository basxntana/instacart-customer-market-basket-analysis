"""Phase 10 - Market Basket Analysis.

Two levels, because they answer different business questions:
  * aisle level   -> which SHELVES travel together (store layout, category bundles)
  * product level -> which SKUs travel together (cross-sell, recommendation)

Both run on a fixed random sample of baskets so support is a share of a clearly
defined universe, and so the run is reproducible.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy import sparse
from mlxtend.frequent_patterns import fpgrowth, association_rules

SEED = 42

def sample_baskets(items: pd.DataFrame, n_baskets: int, seed: int = SEED) -> np.ndarray:
    ids = items.order_id.unique()
    rng = np.random.default_rng(seed)
    if n_baskets >= len(ids):
        return ids
    return rng.choice(ids, n_baskets, replace=False)

def build_matrix(items: pd.DataFrame, basket_ids: np.ndarray, item_col: str,
                 keep_items: np.ndarray | None = None):
    """Sparse boolean basket x item matrix. Rows = every sampled basket (even if it
    holds none of the kept items), so support stays 'share of sampled baskets'."""
    sub = items[items.order_id.isin(basket_ids)]
    if keep_items is not None:
        sub = sub[sub[item_col].isin(keep_items)]
    row_cat = pd.Categorical(sub.order_id, categories=np.sort(basket_ids))
    col_cat = pd.Categorical(sub[item_col])
    M = sparse.csr_matrix(
        (np.ones(len(sub), dtype=bool), (row_cat.codes, col_cat.codes)),
        shape=(len(basket_ids), len(col_cat.categories)), dtype=bool)
    M.sum_duplicates()
    # mlxtend requires string column names for sparse frames
    df = pd.DataFrame.sparse.from_spmatrix(M, columns=[str(c) for c in col_cat.categories])
    return df.astype(pd.SparseDtype(bool, False))

def mine(basket_df: pd.DataFrame, min_support: float, min_confidence: float,
         min_lift: float, max_len: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    freq = fpgrowth(basket_df, min_support=min_support, use_colnames=True, max_len=max_len)
    if freq.empty:
        return freq, freq
    rules = association_rules(freq, num_itemsets=len(basket_df),
                              metric="confidence", min_threshold=min_confidence)
    rules = rules[rules.lift >= min_lift].copy()
    rules["antecedent_n"] = rules.antecedents.map(len)
    rules["consequent_n"] = rules.consequents.map(len)
    return freq, rules.sort_values("lift", ascending=False).reset_index(drop=True)

def label_rules(rules: pd.DataFrame, name_map: dict | None = None) -> pd.DataFrame:
    def fmt(s):
        vals = [name_map.get(x, str(x)) if name_map else str(x) for x in sorted(s, key=str)]
        return " + ".join(vals)
    out = rules.copy()
    out["antecedent"] = out.antecedents.map(fmt)
    out["consequent"] = out.consequents.map(fmt)
    cols = ["antecedent","consequent","support","confidence","lift","leverage",
            "zhangs_metric","antecedent support","consequent support"]
    return out[cols].rename(columns={"antecedent support":"antecedent_support",
                                     "consequent support":"consequent_support",
                                     "zhangs_metric":"zhangs"})

def pair_lift_matrix(basket_df: pd.DataFrame, top_cols: list) -> pd.DataFrame:
    """Pairwise lift among selected columns - the input for the MBA heatmap."""
    M = sparse.csr_matrix(basket_df[top_cols].sparse.to_coo().tocsr(), dtype=np.float32)
    n = M.shape[0]
    co = (M.T @ M).toarray()
    sup = np.asarray(M.sum(axis=0)).ravel() / n
    joint = co / n
    exp = np.outer(sup, sup)
    with np.errstate(divide="ignore", invalid="ignore"):
        lift = np.where(exp > 0, joint / exp, np.nan)
    np.fill_diagonal(lift, np.nan)
    return pd.DataFrame(lift, index=top_cols, columns=top_cols)
