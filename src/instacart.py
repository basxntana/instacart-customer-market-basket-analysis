"""Shared helpers for the Instacart Customer & Market Basket Analysis project.

Keeping paths, loaders and plot styling in one place so every notebook reads the
same data the same way and every chart looks like part of one report.
"""
from __future__ import annotations
import json, pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIGS = REPORTS / "figures"
TABLES = REPORTS / "tables"
for _p in (PROC, FIGS, TABLES):
    _p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- dtypes
DT_ORDERS = {"order_id": "int32", "user_id": "int32", "eval_set": "category",
             "order_number": "int16", "order_dow": "int8",
             "order_hour_of_day": "int8", "days_since_prior_order": "float32"}
DT_ITEMS = {"order_id": "int32", "product_id": "int32",
            "add_to_cart_order": "int16", "reordered": "int8"}

# order_dow has no documented mapping in the Instacart release. 0 and 1 carry the
# weekend-shaped volume peak, so we label 0 = Saturday for readability only and
# flag it as an assumption everywhere it is used.
DOW_LABELS = ["Sat (0)", "Sun (1)", "Mon (2)", "Tue (3)", "Wed (4)", "Thu (5)", "Fri (6)"]

# Catalogue placeholders: these are "unknown category" buckets, not real shelves.
PLACEHOLDER_DEPT_IDS = (21,)        # 'missing'
PLACEHOLDER_AISLE_IDS = (100, 6)    # 'missing', 'other'

# ---------------------------------------------------------------- loaders
def load_raw(name: str) -> pd.DataFrame:
    dt = DT_ORDERS if name == "orders" else (DT_ITEMS if name.startswith("order_products") else None)
    return pd.read_csv(RAW / f"{name}.csv", dtype=dt)

def load_source(name: str) -> pd.DataFrame:
    """Read a source table, using a parquet cache when one exists and building it when not.

    The six source CSVs take ~90s to parse; the cache makes every later notebook start in
    seconds. Falling back to the CSV matters: a fresh checkout has no cache, and the pipeline
    must run from data/raw alone.
    """
    cache = PROC / f"{name.replace('__', '_')}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = load_raw(name)
    df.to_parquet(cache, index=False)
    print(f"  cached {cache.name} from CSV")
    return df


def load_clean(name: str, **kw) -> pd.DataFrame:
    return pd.read_parquet(PROC / f"{name}.parquet", **kw)

def load_lookups():
    """products (enriched) + aisles + departments."""
    return (load_clean("products_clean"), load_clean("aisles_clean"), load_clean("departments_clean"))

# ---------------------------------------------------------------- plotting
# ---- Colour: the validated reference palette from the dataviz skill, used unchanged.
# Caps that come with it and are respected throughout:
#   * bars / adjacent marks  -> at most the first 4 slots
#   * scatter / all-pairs    -> at most the first 3 slots, otherwise facet
#   * aqua/yellow sit under 3:1 on a light surface -> they always carry direct labels
SURFACE = "#FFFFFF"
PALETTE = {
    "ink": "#0B0B0B", "muted": "#52514E", "grid": "#E6E5E1", "surface": SURFACE,
    "s1": "#2A78D6", "s2": "#EB6834", "s3": "#1BAF7A", "s4": "#EDA100",
    "neutral": "#9C9B95",
    # status colours are reserved for state, never reused as a series
    "good": "#008300", "critical": "#E34948",
}
CAT = [PALETTE["s1"], PALETTE["s2"], PALETTE["s3"], PALETTE["s4"]]
# sequential: one hue, light -> dark (blue ramp steps 100..700)
SEQ = ["#CDE2FB", "#9EC5F4", "#6DA7EC", "#3987E5", "#256ABF", "#184F95", "#0D366B"]
# diverging: blue <-> red with a neutral grey midpoint
DIV = ["#0D366B", "#256ABF", "#6DA7EC", "#CDE2FB", "#F0EFEC", "#F3B4B4", "#E34948", "#A32A29"]

def seq_cmap(name="instacart_seq"):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(name, SEQ)

def div_cmap(name="instacart_div"):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(name, DIV)

def set_style():
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    mpl.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.size": 10.5, "axes.titlesize": 12.5, "axes.titleweight": "600",
        "axes.labelsize": 10, "axes.labelcolor": PALETTE["muted"],
        "axes.edgecolor": PALETTE["grid"], "axes.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlelocation": "left", "axes.titlepad": 12,
        "text.color": PALETTE["ink"],
        "xtick.color": PALETTE["muted"], "ytick.color": PALETTE["muted"],
        "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
        "xtick.bottom": True, "ytick.left": False,
        "grid.color": PALETTE["grid"], "grid.linewidth": 0.8,
        "legend.frameon": False, "legend.fontsize": 9.5,
        "axes.prop_cycle": mpl.cycler(color=CAT),
    })
    return plt

def finish(ax, title=None, subtitle=None, xlabel=None, ylabel=None, source=None, xgrid=False):
    """Title/subtitle/footnote pattern used across every figure in this report."""
    if title:
        ax.set_title(title, pad=26 if subtitle else 12)
        if subtitle:
            # offset in POINTS, not axes fraction: an axes-fraction offset drifts into the
            # title on tall figures and away from it on short ones.
            ax.annotate(subtitle, xy=(0, 1), xycoords="axes fraction",
                        xytext=(0, 7), textcoords="offset points",
                        fontsize=9.5, color=PALETTE["muted"], va="bottom", ha="left")
    ax.set_xlabel(xlabel or ""); ax.set_ylabel(ylabel or "")
    ax.grid(axis="x" if xgrid else "y", alpha=.9)
    ax.set_axisbelow(True)
    if source:
        ax.annotate(source, xy=(0, 0), xycoords="axes fraction",
                    xytext=(0, -38), textcoords="offset points",
                    fontsize=8.5, color=PALETTE["muted"], va="top", ha="left")
    return ax

def savefig(fig, name: str):
    out = FIGS / f"{name}.png"
    fig.savefig(out)
    print(f"  figure -> reports/figures/{name}.png")
    return out

def savetable(df: pd.DataFrame, name: str, index=False):
    out = TABLES / f"{name}.csv"
    df.to_csv(out, index=index)
    print(f"  table  -> reports/tables/{name}.csv  ({len(df):,} rows)")
    return out

# ---------------------------------------------------------------- misc
def pct(x, d=1):
    return f"{x:.{d}f}%"

def fmt(n):
    return f"{n:,.0f}"

def save_json(obj, name: str):
    path = REPORTS / f"{name}.json"
    json.dump(obj, open(path, "w"), indent=2, default=float)
    print(f"  json   -> reports/{name}.json")
    return path

def load_json(name: str):
    return json.load(open(REPORTS / f"{name}.json"))

def map_by_id(keys: np.ndarray, id_col: np.ndarray, val_col: np.ndarray, fill=0, dtype=None):
    """Fast lookup for dense integer keys (product_id / order_id) without a merge."""
    size = int(max(id_col.max(), keys.max())) + 1
    lut = np.full(size, fill, dtype=dtype or val_col.dtype)
    lut[id_col] = val_col
    return lut[keys]
