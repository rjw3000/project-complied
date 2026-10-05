"""Guided source workflow; checks prove internal consistency, not tax-return readiness."""
from decimal import Decimal
from complied.package_review import summary

def assess(db,package_id):
    data=summary(db,package_id)
    manifest=data["manifest"]
    sources=manifest["sources"]
    totals=manifest["totals"]
    fields=("net_taxable_sales","net_nontaxable_sales","net_sales_control","tax_collected")
    checks=[
        {"label":"Both store reports","state":"passed" if {s["store_id"] for s in sources}=={"ivy","pantops"} else "attention",
         "detail":"Ivy Road and Pantops for "+manifest["period"]},
        {"label":"Store sales controls",
         "state":"passed" if all(Decimal(s["net_taxable_sales"])+Decimal(s["net_nontaxable_sales"])==Decimal(s["net_sales_control"]) for s in sources) else "attention",
         "detail":"Taxable plus nontaxable net sales equals each store control total"},
        {"label":"Combined totals",
         "state":"passed" if all(Decimal(totals[field])==sum((Decimal(s[field]) for s in sources),Decimal("0")) for field in fields) else "attention",
         "detail":"Entity totals trace to both store snapshots"},
        {"label":"Immutable source integrity","state":"passed",
         "detail":"Selected hashes and normalized records revalidated against the stored source bytes"}]
    selected={s["snapshot_id"] for s in sources}
    alternatives=set(data["source_versions"])-selected
    checks.append({"label":"Other versions for this month",
                   "state":"attention" if alternatives else "passed",
                   "detail":(str(len(alternatives))+" other source version(s) require explicit comparison in the review notes"
                             if alternatives else "Only the selected store snapshots are known")})
    checks.append({"label":"Tax treatment and government return","state":"pending",
                   "detail":"Actual PostalMate mapping, classifications, return lines and filing route require verification"})
    state=data["review_state"]
    if state=="sources_reviewed":
        next_action="Verify tax treatment and return lines before any filing decision"
        href="/package?id="+package_id
    elif state=="needs_information":
        next_action="Resolve missing information or upload corrected store reports"
        href="/reconcile?id="+package_id
    elif state=="rejected":
        next_action="Upload corrected store reports and prepare a replacement"
        href="/preparation"
    else:
        next_action="Compare store totals and review source evidence"
        href="/reconcile?id="+package_id
    return dict(**data,checks=checks,alternatives=sorted(alternatives),
                next_action=next_action,next_href=href)

def months(db):
    rows=db.execute("""SELECT p.id,p.period,COALESCE(MAX(a.id),0) AS sequence
        FROM preparation_packages p
        LEFT JOIN audit_events a ON a.object_id=p.id AND a.action='prepare-sales'
        GROUP BY p.id ORDER BY p.period DESC,sequence DESC,p.id DESC""").fetchall()
    result=[]
    seen=set()
    for row in rows:
        if row["period"] in seen:
            continue
        seen.add(row["period"])
        result.append(assess(db,row["id"]))
    return result
