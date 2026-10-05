"""Explicit reviewed schedules for synthetic local development, not tax rules."""
import argparse
import calendar
import hashlib
import json
import re
from datetime import date, timedelta

SCHEMA = """
CREATE TABLE IF NOT EXISTS deadline_rules(
 id TEXT PRIMARY KEY, obligation_id TEXT NOT NULL REFERENCES obligations(id),
 definition TEXT NOT NULL, source TEXT NOT NULL, reviewer TEXT NOT NULL,
 reviewed_on TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS task_rules(
 task_id INTEGER PRIMARY KEY REFERENCES tasks(id),
 rule_id TEXT NOT NULL REFERENCES deadline_rules(id));
CREATE TRIGGER IF NOT EXISTS deadline_rules_immutable_update
 BEFORE UPDATE ON deadline_rules BEGIN SELECT RAISE(ABORT,'Rules are immutable'); END;
CREATE TRIGGER IF NOT EXISTS deadline_rules_immutable_delete
 BEFORE DELETE ON deadline_rules BEGIN SELECT RAISE(ABORT,'Rules are immutable'); END;
"""

def migrate(db):
    # Additive migration preserves v1 obligations, tasks and completion history.
    db.executescript(SCHEMA)
    with db:
        db.execute("INSERT OR IGNORE INTO schema_versions VALUES(2)")

def iso(value):
    if not isinstance(value,str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}",value):
        raise ValueError("Expected canonical ISO date")
    return date.fromisoformat(value)

def month_add(start, count):
    index = start.year * 12 + start.month - 1 + count
    return date(index // 12,index % 12 + 1,1)

def validate(definition):
    required = {"anchor","period_months","due_month_offset","due_day","short_month",
                "roll","holidays","calendar_start","calendar_end","effective_start","effective_end"}
    if set(definition) != required:
        raise ValueError("Rule fields must match the documented contract")
    anchor = iso(definition["anchor"])
    if anchor.day != 1:
        raise ValueError("Anchor must be first of month")
    if type(definition["period_months"]) is not int or definition["period_months"] not in (1,3,12):
        raise ValueError("Period must be 1, 3 or 12 months")
    if type(definition["due_month_offset"]) is not int or not 0 <= definition["due_month_offset"] <= 12:
        raise ValueError("Offset must be 0..12 months after the period")
    if type(definition["due_day"]) is not int or not 1 <= definition["due_day"] <= 31:
        raise ValueError("Due day must be 1..31")
    if definition["short_month"] not in ("reject","last_day"):
        raise ValueError("Short month policy must be explicit")
    if definition["roll"] not in ("none","next_business_day"):
        raise ValueError("Unsupported roll policy")
    start,end = iso(definition["effective_start"]),iso(definition["effective_end"])
    if start.day != 1 or end.day != 1 or start > end:
        raise ValueError("Effective range uses ordered period-start months")
    if not isinstance(definition["holidays"],list):
        raise ValueError("Holidays must be an explicit list")
    for holiday in definition["holidays"]:
        iso(holiday)
    if definition["roll"] == "next_business_day":
        lower,upper = iso(definition["calendar_start"]),iso(definition["calendar_end"])
        if lower > upper or any(not lower <= iso(h) <= upper for h in definition["holidays"]):
            raise ValueError("Holiday calendar coverage is invalid")
    elif definition["calendar_start"] is not None or definition["calendar_end"] is not None or definition["holidays"]:
        raise ValueError("No-roll policy must not imply use of a holiday calendar")

def due_date(definition, period):
    validate(definition)
    start = iso(period + "-01")
    anchor = iso(definition["anchor"])
    delta = (start.year-anchor.year)*12 + start.month-anchor.month
    if delta < 0 or delta % definition["period_months"]:
        raise ValueError("Period is not aligned to rule anchor")
    if not iso(definition["effective_start"]) <= start <= iso(definition["effective_end"]):
        raise ValueError("Period is outside rule effective range")
    target = month_add(start,definition["period_months"] + definition["due_month_offset"])
    last = calendar.monthrange(target.year,target.month)[1]
    day = definition["due_day"]
    if day > last:
        if definition["short_month"] == "reject":
            raise ValueError("Due day absent in target month")
        day = last
    result = target.replace(day=day)
    if definition["roll"] == "next_business_day":
        lower,upper = iso(definition["calendar_start"]),iso(definition["calendar_end"])
        while True:
            if not lower <= result <= upper:
                raise ValueError("Deadline outside reviewed calendar coverage")
            if result.weekday() < 5 and result.isoformat() not in definition["holidays"]:
                break
            result += timedelta(days=1)
    return result.isoformat()

def register_rule(db, obligation_id, definition, *, source, reviewer, reviewed_on):
    validate(definition)
    iso(reviewed_on)
    if not source.strip() or not reviewer.strip():
        raise ValueError("Rule source and reviewer required")
    obligation = db.execute("SELECT * FROM obligations WHERE id=?",(obligation_id,)).fetchone()
    if obligation is None or obligation["status"] != "applicable" or not obligation["reviewed"]:
        raise ValueError("Obligation must be applicable and reviewed")
    content = dict(obligation_id=obligation_id,definition=definition,source=source,
                   reviewer=reviewer,reviewed_on=reviewed_on)
    canonical = json.dumps(content,sort_keys=True,separators=(",",":"))
    rule_id = hashlib.sha256(canonical.encode()).hexdigest()
    with db:
        db.execute("INSERT OR IGNORE INTO deadline_rules VALUES(?,?,?,?,?,?)",
                   (rule_id,obligation_id,json.dumps(definition,sort_keys=True),source,reviewer,reviewed_on))
    return rule_id

def generate(db, rule_id, first_period, count):
    if type(count) is not int or not 1 <= count <= 120:
        raise ValueError("Count must be 1..120")
    start = iso(first_period+"-01")
    if db.in_transaction:
        raise ValueError("Generation requires its own transaction")
    # Serialize against competing generators and roll back the whole requested batch.
    db.execute("BEGIN IMMEDIATE")
    try:
        rule = db.execute("SELECT * FROM deadline_rules WHERE id=?",(rule_id,)).fetchone()
        if rule is None:
            raise ValueError("Unknown rule")
        obligation = db.execute("SELECT * FROM obligations WHERE id=?",(rule["obligation_id"],)).fetchone()
        if obligation["status"] != "applicable" or not obligation["reviewed"]:
            raise ValueError("Obligation review is no longer valid")
        definition = json.loads(rule["definition"])
        ids = []
        for index in range(count):
            period = month_add(start,index*definition["period_months"]).strftime("%Y-%m")
            due = due_date(definition,period)
            existing = db.execute("""SELECT t.id,t.due_date,tr.rule_id FROM tasks t
                 LEFT JOIN task_rules tr ON tr.task_id=t.id
                 WHERE t.obligation_id=? AND t.period=?""",(rule["obligation_id"],period)).fetchone()
            if existing:
                if existing["due_date"] != due or existing["rule_id"] != rule_id:
                    raise ValueError("Existing task conflicts with rule; explicit reconciliation required")
                ids.append(existing["id"])
                continue
            task_id = db.execute("INSERT INTO tasks(obligation_id,period,due_date) VALUES(?,?,?)",
                                 (rule["obligation_id"],period,due)).lastrowid
            db.execute("INSERT INTO task_rules VALUES(?,?)",(task_id,rule_id))
            ids.append(task_id)
        db.commit()
        return ids
    except Exception:
        db.rollback()
        raise

def demo(db):
    from complied.deadlines import add_obligation
    if not db.execute("SELECT 1 FROM obligations WHERE id='demo-recurring'").fetchone():
        add_obligation(db,id="demo-recurring",title="Demo recurring duty",jurisdiction="Synthetic",
                       owner="Demo owner",status="applicable",source="urn:synthetic:fixture",reviewed=True)
    definition = dict(anchor="2026-01-01",period_months=1,due_month_offset=0,due_day=15,
                      short_month="reject",roll="none",holidays=[],calendar_start=None,calendar_end=None,
                      effective_start="2026-01-01",effective_end="2027-12-01")
    rule = register_rule(db,"demo-recurring",definition,source="urn:synthetic:fixture",
                         reviewer="Demo reviewer",reviewed_on="2026-10-05")
    return generate(db,rule,"2026-10",3)

def main():
    from complied.deadlines import connect
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",default="var/demo.sqlite3")
    args = parser.parse_args()
    db = connect(args.db)
    try:
        print(json.dumps({"synthetic_task_ids":demo(db)}))
    finally:
        db.close()

if __name__ == "__main__":
    main()
