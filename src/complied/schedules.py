"""Authenticated schedule preview and reconciliation; no external writes."""
import json
import secrets
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from complied.access import authorize,audit
from complied.recurrence import register_rule,due_date,month_add,iso

def migrate(db):
    db.execute("""CREATE TABLE IF NOT EXISTS schedule_proposals(
        id TEXT PRIMARY KEY,actor TEXT NOT NULL,rule_id TEXT NOT NULL REFERENCES deadline_rules(id),
        first_period TEXT NOT NULL,count INTEGER NOT NULL,reason TEXT NOT NULL,
        preview TEXT NOT NULL,expires INTEGER NOT NULL,consumed INTEGER NOT NULL DEFAULT 0)""")
    with db:
        for table in ("tasks","reminder_outbox"):
            if "schedule_revision" not in {r["name"] for r in db.execute("PRAGMA table_info("+table+")")}:
                db.execute("ALTER TABLE "+table+" ADD COLUMN schedule_revision INTEGER NOT NULL DEFAULT 0")
        db.execute("INSERT OR IGNORE INTO schema_versions VALUES(5)")

def plan(db,rule_id,first_period,count):
    if type(count) is not int or not 1<=count<=120:
        raise ValueError("Count must be 1..120")
    start=iso(first_period+"-01")
    rule=db.execute("SELECT * FROM deadline_rules WHERE id=?",(rule_id,)).fetchone()
    if rule is None: raise ValueError("Rule missing")
    obligation=db.execute("SELECT * FROM obligations WHERE id=?",(rule["obligation_id"],)).fetchone()
    if obligation["status"]!="applicable" or not obligation["reviewed"] or obligation["revision"]!=rule["obligation_revision"]:
        raise ValueError("Rule does not match current review")
    definition=json.loads(rule["definition"])
    rows=[]
    for index in range(count):
        period=month_add(start,index*definition["period_months"]).strftime("%Y-%m")
        due=due_date(definition,period)
        existing=db.execute("""SELECT t.*,tr.rule_id FROM tasks t LEFT JOIN task_rules tr ON tr.task_id=t.id
                               WHERE obligation_id=? AND period=?""",(rule["obligation_id"],period)).fetchone()
        old=dict(existing) if existing else None
        reminders=[dict(r) for r in db.execute("SELECT id,channel,status,provider_id FROM reminder_outbox WHERE task_id=? ORDER BY id",(existing["id"],))] if existing else []
        action="create"
        if existing:
            if existing["due_date"]==due and existing["rule_id"]==rule_id and existing["obligation_revision"]==obligation["revision"]:
                action="keep"
            elif existing["completed_on"]:
                action="blocked_completed"
            elif any(r["status"] in ("inflight","unknown") or (r["channel"]=="calendar" and r["status"]=="created") for r in reminders):
                action="blocked_external"
            else:
                action="replace"
        rows.append(dict(period=period,due_date=due,action=action,before=old,reminders=reminders))
    return dict(rule_id=rule_id,obligation_id=obligation["id"],revision=obligation["revision"],rows=rows)

def propose(db,token,obligation_id,definition,source,first_period,count,reason):
    user=authorize(db,token,"review")
    if not reason.strip() or len(reason)>2000: raise ValueError("Rationale required")
    rule_id=register_rule(db,obligation_id,definition,source=source,reviewer=user["id"],
                         reviewed_on=datetime.now(ZoneInfo("America/New_York")).date().isoformat())
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authorize(db,token,"review")
        preview=plan(db,rule_id,first_period,count)
        proposal=secrets.token_hex(24)
        db.execute("INSERT INTO schedule_proposals VALUES(?,?,?,?,?,?,?,?,0)",
                   (proposal,user["id"],rule_id,first_period,count,reason,json.dumps(preview,sort_keys=True),int(time.time())+900))
        audit(db,user,"preview-schedule",proposal,{"rule_id":rule_id,"reason":reason})
        db.commit()
        return proposal,preview
    except Exception:
        db.rollback()
        raise

def confirm(db,token,proposal_id):
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authorize(db,token,"review")
        proposal=db.execute("SELECT * FROM schedule_proposals WHERE id=?",(proposal_id,)).fetchone()
        if not proposal or proposal["actor"]!=user["id"] or proposal["consumed"] or proposal["expires"]<=int(time.time()):
            raise ValueError("Preview expired, consumed or belongs to another reviewer")
        current=plan(db,proposal["rule_id"],proposal["first_period"],proposal["count"])
        if json.dumps(current,sort_keys=True)!=proposal["preview"]:
            raise ValueError("Tasks changed; preview again")
        if any(row["action"].startswith("blocked") for row in current["rows"]):
            raise ValueError("Completed or externally uncertain task needs separate reconciliation")
        for row in current["rows"]:
            if row["action"]=="keep": continue
            if row["action"]=="create":
                task_id=db.execute("""INSERT INTO tasks(obligation_id,period,due_date,obligation_revision)
                                      VALUES(?,?,?,?)""",(current["obligation_id"],row["period"],row["due_date"],current["revision"])).lastrowid
                db.execute("INSERT INTO task_rules VALUES(?,?)",(task_id,current["rule_id"]))
            else:
                task_id=row["before"]["id"]
                db.execute("UPDATE tasks SET due_date=?,obligation_revision=?,schedule_revision=schedule_revision+1 WHERE id=?",
                           (row["due_date"],current["revision"],task_id))
                db.execute("INSERT OR REPLACE INTO task_rules VALUES(?,?)",(task_id,current["rule_id"]))
                db.execute("UPDATE reminder_outbox SET status='cancelled',error='Schedule replaced after review' WHERE task_id=? AND status='queued'",(task_id,))
            audit(db,user,"apply-schedule",str(task_id),dict(row,rule_id=current["rule_id"],reason=proposal["reason"]))
        db.execute("UPDATE schedule_proposals SET consumed=1 WHERE id=?",(proposal_id,))
        db.commit()
        return current
    except Exception:
        db.rollback()
        raise
