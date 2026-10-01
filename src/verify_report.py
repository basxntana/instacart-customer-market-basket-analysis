"""Guard: re-check every headline figure quoted in README.md and reports/final_report.md
against the generated tables. Run after any re-run of the notebooks; exits non-zero on drift."""
import pandas as pd, pathlib, sys
T = pathlib.Path(__file__).resolve().parents[1] / "reports" / "tables"
L = lambda n: pd.read_csv(T/f"{n}.csv")
kpi = L("kpi_overall"); K = dict(zip(kpi.kpi, kpi.value))
dept, aisle, prod = L("department_kpis"), L("aisle_kpis"), L("product_kpis")
quad, seg, ron = L("product_quadrants"), L("customer_segments"), L("reorder_by_order_number")
hour, dow, dspo = L("orders_by_hour"), L("orders_by_dow"), L("orders_by_days_since_prior")
bsz, rten = L("basket_size_distribution"), L("reorder_by_customer_tenure")
rules, arule = L("mba_rules_product"), L("mba_rules_aisle")

rr = lambda n: float(ron.loc[ron.order_number == n, "reorder_rate"].iat[0])
core = quad[quad.quadrant.str.startswith("Core")]
banana = prod.nlargest(1, "purchases").iloc[0]
pasta = arule[(arule.antecedent == "dry pasta") & (arule.consequent == "pasta sauce")].iloc[0]
herbs = arule[(arule.antecedent == "fresh herbs") & (arule.consequent == "fresh vegetables")].iloc[0]
pr = dept[dept.department == "produce"].iloc[0]
de = dept[dept.department == "dairy eggs"].iloc[0]
cell = lambda df, c, v, col: float(df[df[c] == v][col].iat[0])

CHECKS = [
 ("customers = 206,209", K["Total customers"], 206209, .5),
 ("orders = 3,421,083", K["Total orders (all)"], 3421083, .5),
 ("items = 33,819,106", K["Total items purchased"], 33819106, .5),
 ("avg basket = 10.1", K["Average basket size"], 10.1, .05),
 ("reorder rate = 59.0%", K["Reorder rate (all items)"], 59.0, .05),
 ("reorder excl first = 62.9%", K["Reorder rate (excl. first orders)"], 62.9, .05),
 ("reorder at order 2 = 27.2%", rr(2)*100, 27.2, .05),
 ("reorder at order 6 = 54.1%", rr(6)*100, 54.1, .05),
 ("reorder at order 50 = 81.9%", rr(50)*100, 81.9, .05),
 ("09-16h share = 64.9%", hour.query("9<=order_hour_of_day<=16").order_share.sum()*100, 64.9, .05),
 ("day0+day1 = 34.7%", dow.query("order_dow<=1").order_share.sum()*100, 34.7, .05),
 ("within 7 days = 50.9%", dspo.query("days_since_prior_order<=7").order_share.sum()*100, 50.9, .05),
 ("day-7 spike = 10.0%", float(dspo.query("days_since_prior_order==7").order_share.iat[0])*100, 10.0, .05),
 ("produce units share = 29.2%", pr.units_share*100, 29.2, .05),
 ("produce penetration = 74.9%", pr.basket_penetration*100, 74.9, .05),
 ("dairy reorder = 67.0%", de.reorder_rate*100, 67.0, .05),
 ("milk aisle reorder = 78.2%", cell(aisle, "aisle", "milk", "reorder_rate")*100, 78.2, .05),
 ("spices reorder = 15.3%", cell(aisle, "aisle", "spices seasonings", "reorder_rate")*100, 15.3, .05),
 ("banana units = 491,291", banana.purchases, 491291, .5),
 ("banana reorder = 84.5%", banana.reorder_rate*100, 84.5, .05),
 ("banana customers = 76,125", banana.n_customers, 76125, .5),
 ("core staples count = 2,537", len(core), 2537, .5),
 ("core staples unit share = 67.5%", core.purchases.sum()/quad.purchases.sum()*100, 67.5, .05),
 ("top milk reorder = 86.1%", prod[prod.purchases >= 2000].reorder_rate.max()*100, 86.1, .05),
 ("1-3 item orders = 17.1%", cell(bsz, "bucket", "1-3", "order_share")*100, 17.1, .05),
 ("1-3 item units = 3.5%", cell(bsz, "bucket", "1-3", "item_share")*100, 3.5, .05),
 ("1-3 reorder = 65.0%", cell(bsz, "bucket", "1-3", "reorder_rate")*100, 65.0, .05),
 ("product rules = 3,048", len(rules), 3048, .5),
 ("aisle rules = 3,692", len(arule), 3692, .5),
 ("max product lift = 75.6", rules.lift.max(), 75.6, .05),
 ("pasta->sauce lift = 4.41", pasta.lift, 4.41, .005),
 ("pasta->sauce support = 1.95%", pasta.support*100, 1.95, .005),
 ("herbs->veg confidence = 84.6%", herbs.confidence*100, 84.6, .05),
 ("herbs->veg lift = 1.90", herbs.lift, 1.90, .005),
 ("banana consequent share = 21.5%", rules.consequent.str.contains("Banana", case=False).mean()*100, 21.5, .05),
 ("Loyal Regulars items = 53.4%", cell(seg, "segment", "Loyal Regulars", "item_share")*100, 53.4, .05),
 ("At-Risk customers = 31.9%", cell(seg, "segment", "Occasional / At-Risk", "customer_share")*100, 31.9, .05),
 ("At-Risk items = 8.9%", cell(seg, "segment", "Occasional / At-Risk", "item_share")*100, 8.9, .05),
 ("tenure 3-4 reorder = 24.0%", cell(rten, "bucket", "3-4 orders", "reorder_rate")*100, 24.0, .05),
 ("tenure 51-100 reorder = 75.2%", cell(rten, "bucket", "51-100", "reorder_rate")*100, 75.2, .05),
]

bad = 0
for name, got, want, tol in CHECKS:
    ok = abs(float(got) - float(want)) <= tol
    bad += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {name:<36} got {float(got):,.4f}")
print(f"\n{len(CHECKS)-bad}/{len(CHECKS)} headline figures verified")
sys.exit(1 if bad else 0)
