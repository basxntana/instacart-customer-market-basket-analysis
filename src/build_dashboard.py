"""Phase 17 — Excel dashboard built from the analysis outputs in reports/tables."""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import instacart as ic
import xlsxwriter

T = ic.TABLES
OUT = ic.ROOT / "dashboard" / "instacart_dashboard.xlsx"
OUT.parent.mkdir(exist_ok=True)

# ---------------------------------------------------------------- data
kpi   = pd.read_csv(T/"kpi_overall.csv")
hour  = pd.read_csv(T/"orders_by_hour.csv")
dow   = pd.read_csv(T/"orders_by_dow.csv")
dspo  = pd.read_csv(T/"orders_by_days_since_prior.csv")
prod  = pd.read_csv(T/"product_kpis.csv")
dept  = pd.read_csv(T/"department_kpis.csv")
aisle = pd.read_csv(T/"aisle_kpis.csv")
seg   = pd.read_csv(T/"customer_segments.csv")
ron   = pd.read_csv(T/"reorder_by_order_number.csv")
rten  = pd.read_csv(T/"reorder_by_customer_tenure.csv")
quad  = pd.read_csv(T/"product_quadrants.csv")
rules = pd.read_csv(T/"mba_rules_product.csv")
arule = pd.read_csv(T/"mba_rules_aisle.csv")
bsz   = pd.read_csv(T/"basket_size_distribution.csv")
freq  = pd.read_csv(T/"customer_order_frequency.csv")
K = dict(zip(kpi.kpi, kpi.value))

wb = xlsxwriter.Workbook(OUT, {"nan_inf_to_errors": True})

INK, MUT, GRID = "#0B0B0B", "#52514E", "#E6E5E1"
S1, S2, S3, S4 = "#2A78D6", "#EB6834", "#1BAF7A", "#EDA100"
f = lambda **kw: wb.add_format(kw)
F = {
 "title":    f(font_size=22, bold=True, font_color=INK, font_name="Calibri"),
 "sub":      f(font_size=11, font_color=MUT, font_name="Calibri"),
 "h2":       f(font_size=13, bold=True, font_color=INK, font_name="Calibri", bottom=1, border_color=GRID),
 "kpi_lbl":  f(font_size=9.5, font_color=MUT, font_name="Calibri", align="center", valign="vcenter", bg_color="#F5F7FA"),
 "kpi_val":  f(font_size=21, bold=True, font_color=S1, font_name="Calibri", align="center", valign="vcenter", bg_color="#F5F7FA"),
 "kpi_sub":  f(font_size=8.5, font_color=MUT, font_name="Calibri", align="center", valign="vcenter", bg_color="#F5F7FA"),
 "insight":  f(font_size=10, font_color=INK, font_name="Calibri", text_wrap=True, valign="top", bg_color="#FFF6EE", left=5, border_color=S2),
 "note":     f(font_size=9, font_color=MUT, font_name="Calibri", text_wrap=True, valign="top"),
 "hdr":      f(font_size=10, bold=True, font_color="#FFFFFF", bg_color=S1, border=1, border_color="#FFFFFF", text_wrap=True, valign="vcenter"),
 "cell":     f(font_size=10, font_name="Calibri"),
 "num":      f(font_size=10, num_format="#,##0"),
 "pct":      f(font_size=10, num_format="0.0%"),
 "dec":      f(font_size=10, num_format="0.00"),
 "footer":   f(font_size=8.5, font_color=MUT, italic=True),
}

# ---------------------------------------------------------------- hidden data sheets
def sheet(name, df, hide=True, widths=None, fmts=None):
    ws = wb.add_worksheet(name)
    if hide: ws.hide()
    for j, c in enumerate(df.columns):
        ws.write(0, j, str(c), F["hdr"])
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            fmt = (fmts or {}).get(df.columns[j], F["cell"])
            if isinstance(v, (int, np.integer)): ws.write_number(i, j, int(v), fmt)
            elif isinstance(v, (float, np.floating)):
                ws.write_number(i, j, float(v), fmt) if np.isfinite(v) else ws.write_blank(i, j, None)
            else: ws.write(i, j, str(v), fmt)
    for j, c in enumerate(df.columns):
        ws.set_column(j, j, (widths or {}).get(c, max(11, min(42, len(str(c))+4))))
    ws.autofilter(0, 0, len(df), len(df.columns)-1)
    ws.freeze_panes(1, 0)
    return ws

dow_lbl = ["Day 0 (Sat)","Day 1 (Sun)","Day 2 (Mon)","Day 3 (Tue)","Day 4 (Wed)","Day 5 (Thu)","Day 6 (Fri)"]
d_dow  = dow.assign(day=dow_lbl)[["day","orders","avg_basket","reorder_rate"]]
d_hour = hour[["order_hour_of_day","orders","avg_basket","reorder_rate"]]
d_prod = prod.head(15)[["product_name","purchases","reorders","reorder_rate","n_customers","department"]]
d_rr   = prod[prod.purchases>=2000].nlargest(15,"reorder_rate")[["product_name","department","purchases","reorder_rate"]]
d_dept = dept[~dept.is_placeholder][["department","units","units_share","basket_penetration","reorder_rate","n_products"]]
d_aisle= aisle[~aisle.is_placeholder].head(15)[["aisle","units","units_share","basket_penetration","reorder_rate"]]
d_rule = (rules.nlargest(400,"lift")[["antecedent","consequent","support","confidence","lift"]])
d_arul = (arule[(arule.antecedent.str.count(r"\+")==0)&(arule.consequent.str.count(r"\+")==0)]
          .nlargest(150,"lift")[["antecedent","consequent","support","confidence","lift"]])
d_quad = quad.groupby("quadrant").agg(products=("product_uid","size"), units=("purchases","sum"),
                                      avg_reorder=("reorder_rate","mean")).reset_index()
d_quad["unit_share"] = d_quad.units/d_quad.units.sum()
d_quad = d_quad.sort_values("units", ascending=False)

sheet("d_hour", d_hour); sheet("d_dow", d_dow); sheet("d_dspo", dspo[["days_since_prior_order","orders","reorder_rate"]])
sheet("d_prod", d_prod); sheet("d_rr", d_rr); sheet("d_dept", d_dept); sheet("d_aisle", d_aisle)
sheet("d_seg", seg[["segment","customers","customer_share","item_share","avg_orders","avg_basket","reorder_rate","avg_interval"]])
sheet("d_ron", ron[["order_number","reorder_rate","avg_basket"]])
sheet("d_rten", rten[["bucket","reorder_rate","customers","items"]])
sheet("d_arul", d_arul); sheet("d_quad", d_quad); sheet("d_bsz", bsz[["bucket","orders","order_share","item_share","reorder_rate"]])
sheet("d_freq", freq[["bucket","customers","customer_share","item_share","reorder_rate"]])

# ---------------------------------------------------------------- DASHBOARD
ws = wb.add_worksheet("Dashboard")
ws.activate(); ws.hide_gridlines(2); ws.set_zoom(85)
for col, w in [("A",2.2),("B",15),("C",15),("D",15),("E",15),("F",15),("G",15),("H",15),
               ("I",15),("J",15),("K",15),("L",15),("M",15),("N",15),("O",15),("P",15),("Q",2.2)]:
    ws.set_column(f"{col}:{col}", w)

ws.merge_range("B2:P2", "INSTACART CUSTOMER ANALYTICS", F["title"])
ws.merge_range("B3:P3",
    "206,209 customers · 3,421,083 orders · 33,819,106 items · Instacart Online Grocery Shopping Dataset 2017   "
    "|   Item-level metrics use the 3,346,083 orders whose contents were released; order timing uses all 3,421,083.",
    F["sub"])

# --- KPI tiles
tiles = [
    ("CUSTOMERS",      f"{K['Total customers']:,.0f}",            "distinct user_id"),
    ("ORDERS",         f"{K['Total orders (all)']:,.0f}",         "16.6 per customer (median 10)"),
    ("ITEMS SOLD",     f"{K['Total items purchased']/1e6:,.1f}M", "basket lines"),
    ("AVG BASKET",     f"{K['Average basket size']:.1f}",         "items per order (median 8)"),
    ("REORDER RATE",   f"{K['Reorder rate (all items)']:.1f}%",   "62.9% excl. first orders"),
]
cols = ["B","D","F","H","J"]
span = {"B":"B5:C5","D":"D5:E5","F":"F5:G5","H":"H5:I5","J":"J5:K5"}
span2= {"B":"B6:C7","D":"D6:E7","F":"F6:G7","H":"H6:I7","J":"J6:K7"}
span3= {"B":"B8:C8","D":"D8:E8","F":"F8:G8","H":"H8:I8","J":"J8:K8"}
for (lbl, val, sub), c in zip(tiles, cols):
    ws.merge_range(span[c], lbl, F["kpi_lbl"])
    ws.merge_range(span2[c], val, F["kpi_val"])
    ws.merge_range(span3[c], sub, F["kpi_sub"])
ws.set_row(5, 14); ws.set_row(6, 16); ws.set_row(7, 14)
ws.merge_range("L5:P8",
    "HEADLINE: 59% of everything sold is a product that customer has bought before. "
    "Instacart is a replenishment business, not a discovery business — and the repeat habit "
    "is built between a customer's 2nd and 6th order, where the reorder rate climbs 27% → 54%.",
    F["insight"])

def chart(kind, subtype=None):
    c = wb.add_chart({"type": kind} if not subtype else {"type": kind, "subtype": subtype})
    c.set_legend({"none": True})
    c.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
    c.set_plotarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
    return c

AX = {"line": {"color": GRID}, "major_gridlines": {"visible": True, "line": {"color": GRID}},
      "num_font": {"color": MUT, "size": 9}, "name_font": {"color": MUT, "size": 9}}
AXX = {"line": {"color": GRID}, "num_font": {"color": MUT, "size": 9}, "name_font": {"color": MUT, "size": 9}}

# --- ROW 1: time analysis
ws.merge_range("B10:P10", "WHEN DO CUSTOMERS BUY?", F["h2"])
c1 = chart("column")
c1.add_series({"name": "Orders", "categories": ["d_hour", 1, 0, 24, 0], "values": ["d_hour", 1, 1, 24, 1],
               "fill": {"color": S1}, "gap": 25})
c1.set_title({"name": "Orders by hour of day", "name_font": {"size": 11, "bold": True, "color": INK}})
c1.set_x_axis({**AXX, "name": "hour"}); c1.set_y_axis({**AX})
c1.set_size({"width": 400, "height": 230})
ws.insert_chart("B12", c1)

c2 = chart("column")
c2.add_series({"name": "Orders", "categories": ["d_dow", 1, 0, 7, 0], "values": ["d_dow", 1, 1, 7, 1],
               "fill": {"color": S1}, "gap": 40,
               "points": [{"fill": {"color": S2}}, {"fill": {"color": S2}}]})
c2.set_title({"name": "Orders by day of week", "name_font": {"size": 11, "bold": True, "color": INK}})
c2.set_x_axis({**AXX}); c2.set_y_axis({**AX})
c2.set_size({"width": 370, "height": 230})
ws.insert_chart("H12", c2)

c3 = chart("column")
c3.add_series({"name": "Orders", "categories": ["d_dspo", 1, 0, 31, 0], "values": ["d_dspo", 1, 1, 31, 1],
               "fill": {"color": S1}, "gap": 20})
c3.set_title({"name": "Days since previous order", "name_font": {"size": 11, "bold": True, "color": INK}})
c3.set_x_axis({**AXX, "name": "days"}); c3.set_y_axis({**AX})
c3.set_size({"width": 370, "height": 230})
ws.insert_chart("M12", c3)
ws.merge_range("B25:P25",
    "INSIGHT — 64.9% of orders land between 09:00 and 16:00, and days 0–1 carry 34.7% of the week, "
    "but the two peak days differ in shape (day 0 peaks 13:00–15:00 with 11.2-item baskets; day 1 peaks 09:00–11:00). "
    "Customers run a weekly clock: 50.9% of repeat orders arrive within 7 days and there is a clear spike exactly at day 7.",
    F["insight"])
ws.set_row(24, 30)

# --- ROW 2: products | departments
ws.merge_range("B27:P27", "WHAT DO THEY BUY?", F["h2"])
c4 = chart("bar")
c4.add_series({"name": "Units", "categories": ["d_prod", 1, 0, 10, 0], "values": ["d_prod", 1, 1, 10, 1],
               "fill": {"color": S1}, "gap": 35})
c4.set_title({"name": "Top 10 products by units sold", "name_font": {"size": 11, "bold": True, "color": INK}})
c4.set_x_axis({**AX}); c4.set_y_axis({**AXX, "reverse": True})
c4.set_size({"width": 430, "height": 265})
ws.insert_chart("B29", c4)

c5 = chart("bar")
c5.add_series({"name": "Reorder rate", "categories": ["d_rr", 1, 0, 10, 0], "values": ["d_rr", 1, 3, 10, 3],
               "fill": {"color": S1}, "gap": 35})
c5.set_title({"name": "Highest reorder rate (min 2,000 purchases)", "name_font": {"size": 11, "bold": True, "color": INK}})
c5.set_x_axis({**AX, "num_format": "0%"}); c5.set_y_axis({**AXX, "reverse": True})
c5.set_size({"width": 430, "height": 265})
ws.insert_chart("H29", c5)

c6 = chart("bar")
c6.add_series({"name": "Share of units", "categories": ["d_dept", 1, 0, 10, 0], "values": ["d_dept", 1, 2, 10, 2],
               "fill": {"color": S1}, "gap": 35})
c6.set_title({"name": "Department share of units", "name_font": {"size": 11, "bold": True, "color": INK}})
c6.set_x_axis({**AX, "num_format": "0%"}); c6.set_y_axis({**AXX, "reverse": True})
c6.set_size({"width": 330, "height": 265})
ws.insert_chart("N29", c6)
ws.merge_range("B44:P44",
    "INSIGHT — Produce is 29.2% of all units and appears in 74.9% of baskets, but dairy & eggs has the highest "
    "reorder rate of any department (67.0%). Produce drives traffic; dairy drives the return visit. "
    "The most-reordered products in the catalogue are milk variants (83.9–86.1%) — products people run out of, not products they choose.",
    F["insight"])
ws.set_row(43, 30)

# --- ROW 3: reorder + segments
ws.merge_range("B46:P46", "WHO REPEATS, AND WHEN?", F["h2"])
c7 = chart("line")
c7.add_series({"name": "Reorder rate", "categories": ["d_ron", 1, 0, 50, 0], "values": ["d_ron", 1, 1, 50, 1],
               "line": {"color": S1, "width": 2.25}, "marker": {"type": "none"}})
c7.set_title({"name": "Reorder rate by the customer's nth order", "name_font": {"size": 11, "bold": True, "color": INK}})
c7.set_x_axis({**AXX, "name": "order number"}); c7.set_y_axis({**AX, "num_format": "0%"})
c7.set_size({"width": 400, "height": 250})
ws.insert_chart("B48", c7)

c8 = chart("column")
c8.add_series({"name": "Reorder rate", "categories": ["d_rten", 1, 0, 6, 0], "values": ["d_rten", 1, 1, 6, 1],
               "fill": {"color": S1}, "gap": 40})
c8.set_title({"name": "Reorder rate by customer lifetime orders", "name_font": {"size": 11, "bold": True, "color": INK}})
c8.set_x_axis({**AXX}); c8.set_y_axis({**AX, "num_format": "0%"})
c8.set_size({"width": 370, "height": 250})
ws.insert_chart("H48", c8)

c9 = chart("column")
c9.add_series({"name": "% of customers", "categories": ["d_seg", 1, 0, 4, 0], "values": ["d_seg", 1, 2, 4, 2],
               "fill": {"color": "#9C9B95"}, "gap": 50})
c9.add_series({"name": "% of items bought", "categories": ["d_seg", 1, 0, 4, 0], "values": ["d_seg", 1, 3, 4, 3],
               "fill": {"color": S1}, "gap": 50})
c9.set_title({"name": "Customer segments: size vs value", "name_font": {"size": 11, "bold": True, "color": INK}})
c9.set_x_axis({**AXX}); c9.set_y_axis({**AX, "num_format": "0%"})
c9.set_legend({"position": "bottom", "font": {"size": 9, "color": MUT}})
c9.set_size({"width": 370, "height": 250})
ws.insert_chart("M48", c9)
ws.merge_range("B62:P62",
    "INSIGHT — The reorder habit forms between orders 2 and 6 (27% → 54%), then flattens: that window is where "
    "retention spend pays. 'Loyal Regulars' are 21.6% of customers but 53.4% of items; 'Occasional / At-Risk' are "
    "31.9% of customers and only 8.9% of items. Order frequency and basket size are uncorrelated (ρ=0.06) — they are two separate levers.",
    F["insight"])
ws.set_row(61, 30)

# --- ROW 4: market basket
ws.merge_range("B64:P64", "WHAT SELLS TOGETHER?", F["h2"])
c10 = chart("bar")
c10.add_series({"name": "Lift", "categories": ["d_arul", 1, 0, 10, 0], "values": ["d_arul", 1, 4, 10, 4],
                "fill": {"color": S1}, "gap": 35})
c10.set_title({"name": "Strongest aisle pairings (lift)", "name_font": {"size": 11, "bold": True, "color": INK}})
c10.set_x_axis({**AX}); c10.set_y_axis({**AXX, "reverse": True})
c10.set_size({"width": 430, "height": 255})
ws.insert_chart("B66", c10)

c11 = chart("bar")
c11.add_series({"name": "Units", "categories": ["d_quad", 1, 0, 4, 0], "values": ["d_quad", 1, 4, 4, 4],
                "fill": {"color": S1}, "gap": 35})
c11.set_title({"name": "Share of units by product quadrant", "name_font": {"size": 11, "bold": True, "color": INK}})
c11.set_x_axis({**AX, "num_format": "0%"}); c11.set_y_axis({**AXX, "reverse": True})
c11.set_size({"width": 430, "height": 255})
ws.insert_chart("H66", c11)

c12 = chart("bar")
c12.add_series({"name": "Reorder rate", "categories": ["d_aisle", 1, 0, 10, 0], "values": ["d_aisle", 1, 4, 10, 4],
                "fill": {"color": S1}, "gap": 35})
c12.set_title({"name": "Reorder rate, biggest aisles", "name_font": {"size": 11, "bold": True, "color": INK}})
c12.set_x_axis({**AX, "num_format": "0%"}); c12.set_y_axis({**AXX, "reverse": True})
c12.set_size({"width": 330, "height": 255})
ws.insert_chart("N66", c12)
ws.merge_range("B81:P81",
    "INSIGHT — Dry pasta ↔ pasta sauce is the strongest category pairing (lift 4.41, in 1.95% of baskets) and fresh herbs → "
    "fresh vegetables is the most confident rule found at any level (92.0%). Among best sellers the real cross-sell pairs are "
    "culinary: garlic↔onion (lift 5.64), lime↔lemon (4.08), cucumber↔tomatoes (3.77). Bananas top every confidence ranking and are worth nothing as a recommendation.",
    F["insight"])
ws.set_row(80, 30)

ws.merge_range("B84:P84",
    "Filters: every chart is driven by a named data sheet (d_hour, d_dow, d_prod, d_dept, d_aisle, d_seg, d_rule …). "
    "Unhide any of them (right-click a sheet tab → Unhide) to filter, sort or pivot the underlying figures — each is a "
    "filtered Excel range with the header row frozen. The 'Rules' and 'Data index' tabs are visible and filterable directly.",
    F["note"])
ws.merge_range("B86:P86",
    "Source: Instacart Online Grocery Shopping Dataset 2017 · built by notebooks 01–06 · day-of-week names are an assumption (the source does not document the mapping).",
    F["footer"])

# ---------------------------------------------------------------- visible explorer tabs
sheet("Rules (product)", d_rule, hide=False,
      widths={"antecedent": 46, "consequent": 46},
      fmts={"support": F["pct"], "confidence": F["pct"], "lift": F["dec"]})
sheet("Rules (aisle)", d_arul, hide=False,
      widths={"antecedent": 38, "consequent": 38},
      fmts={"support": F["pct"], "confidence": F["pct"], "lift": F["dec"]})
sheet("Products", prod.head(500)[["product_name","department","aisle","purchases","reorders","reorder_rate","n_customers"]],
      hide=False, widths={"product_name": 46, "aisle": 26},
      fmts={"purchases": F["num"], "reorders": F["num"], "n_customers": F["num"], "reorder_rate": F["pct"]})
sheet("Departments", dept[["department","units","units_share","basket_penetration","reorder_rate","n_products","is_placeholder"]],
      hide=False, fmts={"units": F["num"], "units_share": F["pct"], "basket_penetration": F["pct"],
                        "reorder_rate": F["pct"], "n_products": F["num"]})
sheet("Aisles", aisle[["aisle","units","units_share","basket_penetration","reorder_rate","n_products","is_placeholder"]],
      hide=False, widths={"aisle": 32}, fmts={"units": F["num"], "units_share": F["pct"],
                        "basket_penetration": F["pct"], "reorder_rate": F["pct"], "n_products": F["num"]})
sheet("Segments", seg, hide=False, widths={"segment": 24},
      fmts={"customers": F["num"], "total_items": F["num"], "customer_share": F["pct"],
            "item_share": F["pct"], "reorder_rate": F["pct"]})
sheet("KPIs", kpi, hide=False, widths={"kpi": 44, "definition": 64}, fmts={"value": F["dec"]})

idx = wb.add_worksheet("Data index")
idx.hide_gridlines(2); idx.set_column("A:A", 2); idx.set_column("B:B", 24); idx.set_column("C:C", 86)
idx.write("B2", "What is in this workbook", F["h2"])
rows = [
 ("Dashboard", "The one-page view: KPI tiles, time analysis, product and category performance, reorder analysis, market basket."),
 ("Rules (product)", "Top 400 product association rules by lift. Filter on lift or confidence to find cross-sell candidates."),
 ("Rules (aisle)", "Top 150 aisle-to-aisle rules — the basis for store layout and shopping-mission detection."),
 ("Products", "Top 500 products with volume, reorders, reorder rate and customer reach."),
 ("Departments / Aisles", "Full category performance, including the placeholder flag ('missing'/'other' are NOT real categories)."),
 ("Segments", "The four behavioural customer segments and their profiles."),
 ("KPIs", "Every headline KPI with its exact definition and measurement base."),
 ("d_* (hidden)", "The small ranges that drive each chart. Right-click a tab → Unhide to inspect or re-filter."),
]
for i, (a, b) in enumerate(rows, start=4):
    idx.write(f"B{i}", a, f(font_size=10, bold=True, font_color=INK))
    idx.write(f"C{i}", b, F["note"])
idx.write("B14", "Measurement bases", f(font_size=11, bold=True, font_color=INK))
idx.write("C14", "Order timing (hour, day, interval) uses all 3,421,083 orders. Everything item-level "
                 "(products, categories, reorder rate, basket size) uses the 3,346,083 orders whose contents were "
                 "released — the 75,000 'test' orders have no basket contents in the source data.", F["note"])
idx.write("B16", "Known limits", f(font_size=11, bold=True, font_color=INK))
idx.write("C16", "No prices, margins, dates or customer demographics exist in this dataset, so no revenue figure is "
                 "possible and seasonality cannot be measured. days_since_prior_order is capped at 30 and order_number "
                 "at 100. Day-of-week names are an assumption.", F["note"])

wb.close()
print(f"wrote {OUT}  ({OUT.stat().st_size/1024:.0f} KB)")

# ---------------------------------------------------------------- Power BI model files
PBI = ic.ROOT / "dashboard" / "powerbi_model"
PBI.mkdir(exist_ok=True)
dept.to_csv(PBI/"dim_department.csv", index=False)
aisle.to_csv(PBI/"dim_aisle.csv", index=False)
prod[["product_uid","product_name","aisle","department","purchases","reorders","reorder_rate","n_customers"]].to_csv(PBI/"dim_product.csv", index=False)
seg.to_csv(PBI/"dim_segment.csv", index=False)
hour.to_csv(PBI/"fact_orders_by_hour.csv", index=False)
dow.assign(day=dow_lbl).to_csv(PBI/"fact_orders_by_dow.csv", index=False)
dspo.to_csv(PBI/"fact_orders_by_interval.csv", index=False)
ron.to_csv(PBI/"fact_reorder_by_order_number.csv", index=False)
rules.nlargest(2000,"lift").to_csv(PBI/"fact_association_rules.csv", index=False)
kpi.to_csv(PBI/"kpi_overall.csv", index=False)
print(f"wrote {len(list(PBI.glob('*.csv')))} Power BI model files -> dashboard/powerbi_model/")
