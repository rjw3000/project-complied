"""Synthetic normalized monthly sales imports; no tax calculations or filings."""
import argparse
import csv
import hashlib
import io
import json
import re
from decimal import Decimal
from pathlib import Path
from complied.access import authorize,audit

HEADERS=["store_id","period","net_taxable_sales","net_nontaxable_sales","net_sales_control","tax_collected"]
STORES={"ivy","pantops"}
FORMAT="normalized-monthly-v1"

def migrate(db):
    db.executescript("""
      CREATE TABLE IF NOT EXISTS sales_snapshots(
        id TEXT PRIMARY KEY,store_id TEXT NOT NULL,period TEXT NOT NULL,
        format_version TEXT NOT NULL,raw BLOB NOT NULL,normalized TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS preparation_packages(
        id TEXT PRIMARY KEY,period TEXT NOT NULL,manifest TEXT NOT NULL,created_by TEXT NOT NULL REFERENCES users(id));
      CREATE TRIGGER IF NOT EXISTS snapshots_no_update BEFORE UPDATE ON sales_snapshots
        BEGIN SELECT RAISE(ABORT,'Snapshots are immutable'); END;
      CREATE TRIGGER IF NOT EXISTS snapshots_no_delete BEFORE DELETE ON sales_snapshots
        BEGIN SELECT RAISE(ABORT,'Snapshots are immutable'); END;
      CREATE TRIGGER IF NOT EXISTS packages_no_update BEFORE UPDATE ON preparation_packages
        BEGIN SELECT RAISE(ABORT,'Packages are immutable'); END;
      CREATE TRIGGER IF NOT EXISTS packages_no_delete BEFORE DELETE ON preparation_packages
        BEGIN SELECT RAISE(ABORT,'Packages are immutable'); END;
    """)
    with db: db.execute("INSERT OR IGNORE INTO schema_versions VALUES(6)")

def money(value):
    if not isinstance(value,str) or not re.fullmatch(r"-?[0-9]{1,12}\.[0-9]{2}",value):
        raise ValueError("Money requires fixed decimal strings with two places")
    result=Decimal(value)
    return "0.00" if result==0 else format(result,".2f")

def parse(raw):
    if not isinstance(raw,bytes) or len(raw)>65536:
        raise ValueError("CSV must be bytes, at most 64 KiB")
    text=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text,newline=""))
    if reader.fieldnames!=HEADERS:
        raise ValueError("Expected exact normalized-monthly-v1 headers")
    rows=list(reader)
    if len(rows)!=1 or None in rows[0] or any(value is None for value in rows[0].values()):
        raise ValueError("Exactly one complete store-month row required")
    row=rows[0]
    if row["store_id"] not in STORES or not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])",row["period"]):
        raise ValueError("Known store and canonical period required")
    if row["period"].startswith("0000"):
        raise ValueError("Year must be positive")
    for field in HEADERS[2:]:
        row[field]=money(row[field])
    if Decimal(row["net_taxable_sales"])+Decimal(row["net_nontaxable_sales"])!=Decimal(row["net_sales_control"]):
        raise ValueError("Store net sales do not reconcile to control total")
    return row

def import_snapshot(db,token,raw):
    authorize(db,token,"edit")
    row=parse(raw)
    key=hashlib.sha256(raw).hexdigest()
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authorize(db,token,"edit")
        cursor=db.execute("INSERT OR IGNORE INTO sales_snapshots VALUES(?,?,?,?,?,?)",
                         (key,row["store_id"],row["period"],FORMAT,raw,json.dumps(row,sort_keys=True)))
        if cursor.rowcount:
            audit(db,user,"import-sales",key,{"store":row["store_id"],"period":row["period"],"format":FORMAT})
        db.commit()
        return key
    except Exception:
        db.rollback()
        raise

def assemble(db,snapshot_ids):
    if len(snapshot_ids)!=2 or len(set(snapshot_ids))!=2:
        raise ValueError("Select two distinct source snapshots")
    snapshots=[]
    for key in snapshot_ids:
        row=db.execute("SELECT * FROM sales_snapshots WHERE id=?",(key,)).fetchone()
        if row is None or row["format_version"]!=FORMAT:
            raise ValueError("Snapshot unavailable or unsupported")
        if hashlib.sha256(row["raw"]).hexdigest()!=row["id"]:
            raise ValueError("Snapshot integrity failed")
        normalized=parse(row["raw"])
        if json.loads(row["normalized"])!=normalized:
            raise ValueError("Normalized snapshot mismatch")
        snapshots.append((row["id"],normalized))
    if {row["store_id"] for _,row in snapshots}!=STORES or len({row["period"] for _,row in snapshots})!=1:
        raise ValueError("Both stores from the same month required")
    snapshots.sort(key=lambda item:item[1]["store_id"])
    totals={field:format(sum((Decimal(row[field]) for _,row in snapshots),Decimal("0.00")),".2f")
            for field in HEADERS[2:]}
    manifest=dict(format_version=FORMAT,period=snapshots[0][1]["period"],
                  status="source_reconciled_not_return_ready",
                  sources=[dict(snapshot_id=key,**row) for key,row in snapshots],totals=totals,
                  limitations=["Synthetic normalized contract; actual PostalMate mapping unverified",
                               "No rates, exemptions, return lines or remittance amount calculated"])
    return manifest

def prepare(db,token,snapshot_ids):
    authorize(db,token,"review")
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authorize(db,token,"review")
        manifest=assemble(db,snapshot_ids)
        serialized=json.dumps(manifest,sort_keys=True,separators=(",",":"))
        key=hashlib.sha256(serialized.encode()).hexdigest()
        cursor=db.execute("INSERT OR IGNORE INTO preparation_packages VALUES(?,?,?,?)",
                         (key,manifest["period"],serialized,user["id"]))
        if cursor.rowcount:
            audit(db,user,"prepare-sales",key,{"period":manifest["period"],"snapshots":sorted(snapshot_ids)})
        db.commit()
        return key,manifest
    except Exception:
        db.rollback()
        raise


def import_pair(db,token,ivy_raw,pantops_raw):
    """Atomically import both normalized CSVs and prepare one source package."""
    authorize(db,token,"review")
    rows=[parse(ivy_raw),parse(pantops_raw)]
    if [row["store_id"] for row in rows]!=["ivy","pantops"] or rows[0]["period"]!=rows[1]["period"]:
        raise ValueError("Upload Ivy and Pantops reports for the same month")
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authorize(db,token,"review")
        ids=[]
        for raw,row in zip((ivy_raw,pantops_raw),rows):
            key=hashlib.sha256(raw).hexdigest()
            cursor=db.execute("INSERT OR IGNORE INTO sales_snapshots VALUES(?,?,?,?,?,?)",
                              (key,row["store_id"],row["period"],FORMAT,raw,json.dumps(row,sort_keys=True)))
            if cursor.rowcount:
                audit(db,user,"import-sales",key,{"store":row["store_id"],"period":row["period"],"format":FORMAT})
            ids.append(key)
        manifest=assemble(db,ids)
        serialized=json.dumps(manifest,sort_keys=True,separators=(",",":"))
        key=hashlib.sha256(serialized.encode()).hexdigest()
        cursor=db.execute("INSERT OR IGNORE INTO preparation_packages VALUES(?,?,?,?)",
                          (key,manifest["period"],serialized,user["id"]))
        if cursor.rowcount:
            audit(db,user,"prepare-sales",key,{"period":manifest["period"],"snapshots":sorted(ids)})
        db.commit()
        return key,manifest
    except Exception:
        db.rollback()
        raise

def main():
    import getpass
    from complied.access import login,logout
    from complied.deadlines import connect
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",default="var/demo.sqlite3")
    parser.add_argument("--user",required=True)
    parser.add_argument("files",nargs=2,help="One normalized synthetic CSV for each store")
    args=parser.parse_args()
    db=connect(args.db)
    token=None
    try:
        token,_=login(db,args.user,getpass.getpass("Local account password: "))
        ids=[]
        for filename in args.files:
            with Path(filename).open("rb") as source:
                raw=source.read(65537)
            ids.append(import_snapshot(db,token,raw))
        key,manifest=prepare(db,token,ids)
        print(json.dumps({"package_id":key,**manifest},indent=2))
    finally:
        if token: logout(db,token)
        db.close()

if __name__=="__main__":
    main()
