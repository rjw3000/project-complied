"""Local synthetic obligation register. No tax rules or external execution."""
import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_versions(version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS locations(
 id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, name TEXT NOT NULL, jurisdiction TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS obligations(
 id TEXT PRIMARY KEY, title TEXT NOT NULL, jurisdiction TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('unresolved','applicable','not_applicable')),
 source TEXT NOT NULL DEFAULT '', rationale TEXT NOT NULL DEFAULT '',
 owner TEXT NOT NULL, location_id TEXT REFERENCES locations(id),
 reviewed INTEGER NOT NULL DEFAULT 0 CHECK(reviewed IN (0,1)),
 CHECK(status != 'applicable' OR (reviewed = 1 AND length(source) > 0)));
CREATE TABLE IF NOT EXISTS tasks(
 id INTEGER PRIMARY KEY, obligation_id TEXT NOT NULL REFERENCES obligations(id),
 period TEXT NOT NULL, due_date TEXT, completed_on TEXT,
 UNIQUE(obligation_id,period));
"""

def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    with db:
        db.executescript(SCHEMA)
        db.execute("INSERT OR IGNORE INTO schema_versions VALUES(1)")
    from complied.recurrence import migrate
    migrate(db)
    from complied.access import migrate as migrate_access
    migrate_access(db)
    return db

def add_obligation(db, *, id, title, jurisdiction, owner, status="unresolved",
                   source="", rationale="", location_id=None, reviewed=False):
    if status == "applicable" and (not reviewed or not source.strip()):
        raise ValueError("Applicable obligations need reviewed source evidence")
    if not all(str(v).strip() for v in (id, title, jurisdiction, owner)):
        raise ValueError("Scope and owner are required")
    with db:
        db.execute("INSERT INTO obligations(id,title,jurisdiction,status,source,rationale,owner,location_id,reviewed) VALUES(?,?,?,?,?,?,?,?,?)",
                   (id,title,jurisdiction,status,source,rationale,owner,location_id,int(reviewed)))

def add_task(db, obligation_id, period, due_date=None):
    if not period.strip():
        raise ValueError("Period is required")
    if due_date is not None:
        date.fromisoformat(due_date)
    obligation = db.execute("SELECT * FROM obligations WHERE id=?", (obligation_id,)).fetchone()
    if obligation is None or obligation["status"] == "not_applicable":
        raise ValueError("Task requires an active or unresolved obligation")
    if due_date and (obligation["status"] != "applicable" or not obligation["reviewed"]):
        raise ValueError("Unreviewed obligations cannot have verified deadlines")
    with db:
        db.execute("INSERT OR IGNORE INTO tasks(obligation_id,period,due_date,obligation_revision) VALUES(?,?,?,?)",
                   (obligation_id,period,due_date,obligation["revision"]))
        saved = db.execute("SELECT due_date,obligation_revision FROM tasks WHERE obligation_id=? AND period=?",
                           (obligation_id,period)).fetchone()
        if saved["due_date"] != due_date or saved["obligation_revision"] != obligation["revision"]:
            raise ValueError("Existing deadline differs; explicit reconciliation required")

def complete_task(db, task_id, completed_on):
    date.fromisoformat(completed_on)
    row = db.execute("""SELECT o.status,o.reviewed,o.revision,t.obligation_revision,t.due_date FROM tasks t
                      JOIN obligations o ON o.id=t.obligation_id WHERE t.id=?""", (task_id,)).fetchone()
    if row is None or row["status"] != "applicable" or not row["reviewed"] or row["due_date"] is None or row["revision"] != row["obligation_revision"]:
        raise ValueError("Unresolved tasks cannot be completed")
    with db:
        db.execute("UPDATE tasks SET completed_on=? WHERE id=?", (completed_on,task_id))

def dashboard(db, today):
    """Unknown applicability takes precedence over nominal task dates."""
    rows = db.execute("""SELECT t.id,o.id AS obligation_id,COALESCE(t.period,'No period') AS period,
                         t.due_date,t.completed_on,o.title,o.jurisdiction,o.owner,o.status AS applicability,
                         o.source,o.rationale,o.reviewed,tr.rule_id,o.revision,t.obligation_revision FROM obligations o
                         LEFT JOIN tasks t ON o.id=t.obligation_id
                         LEFT JOIN task_rules tr ON tr.task_id=t.id
                         ORDER BY t.due_date IS NULL,t.due_date,t.id""").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        if item["applicability"] == "not_applicable":
            state = "not_applicable"
        elif item["applicability"] != "applicable" or not item["reviewed"] or not item["due_date"] or item["obligation_revision"] != item["revision"]:
            state = "unresolved"
        elif item["completed_on"]:
            state = "completed"
        elif date.fromisoformat(item["due_date"]) < today:
            state = "overdue"
        elif date.fromisoformat(item["due_date"]) == today:
            state = "due_today"
        else:
            state = "upcoming"
        item["state"] = state
        result.append(item)
    return result

def seed(db):
    """Demo dates only; none of these rows establishes a business deadline."""
    with db:
        db.execute("INSERT OR IGNORE INTO locations VALUES('ivy','demo-llc','Ivy demo','Charlottesville City')")
        db.execute("INSERT OR IGNORE INTO locations VALUES('pantops','demo-llc','Pantops demo','Albemarle County')")
    seeds = [
        ("sales","Monthly sales tax — registration/date review","Virginia",None),
        ("city","Business license — confirm notice","Charlottesville City","ivy"),
        ("county","Business license — confirm notice","Albemarle County","pantops"),
        ("state","State company filing — confirm duty","Virginia",None),
        ("payroll","Payroll duties — discovery","Federal / Virginia",None),
    ]
    for oid,title,jurisdiction,location in seeds:
        if not db.execute("SELECT 1 FROM obligations WHERE id=?", (oid,)).fetchone():
            add_obligation(db,id=oid,title=title,jurisdiction=jurisdiction,owner="Demo owner",
                           location_id=location,rationale="Synthetic discovery seed; legal applicability not established")
        add_task(db,oid,"2026-10")
    for oid,title,due in [
        ("demo-overdue","Demo overdue task","2026-10-01"),
        ("demo-upcoming","Demo upcoming task","2026-10-20"),
        ("demo-completed","Demo completed task","2026-09-30"),
    ]:
        if not db.execute("SELECT 1 FROM obligations WHERE id=?", (oid,)).fetchone():
            add_obligation(db,id=oid,title=title,jurisdiction="Synthetic jurisdiction",
                           owner="Demo owner",status="applicable",source="urn:synthetic:fixture",
                           rationale="UI fixture only; not a government deadline",reviewed=True)
        add_task(db,oid,"demo-period",due)
    task = db.execute("SELECT id FROM tasks WHERE obligation_id='demo-completed'").fetchone()
    complete_task(db,task["id"],"2026-09-29")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["init","seed","list"])
    parser.add_argument("--db",default="var/demo.sqlite3")
    parser.add_argument("--today",default="2026-10-05",help="Demo reference date, ISO format")
    args = parser.parse_args()
    Path(args.db).parent.mkdir(parents=True,exist_ok=True)
    db = connect(args.db)
    try:
        if args.command == "seed":
            seed(db)
        if args.command == "list":
            print(json.dumps(dashboard(db,date.fromisoformat(args.today)),indent=2))
    finally:
        db.close()

if __name__ == "__main__":
    main()
