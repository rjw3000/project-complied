"""Durable Microsoft reminder outbox. Default execution is preview only."""
import hashlib
import json
import time
from datetime import date,datetime,timedelta,timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo
from complied.access import authorize,audit

SCHEMA = """
CREATE TABLE IF NOT EXISTS reminder_settings(
 singleton INTEGER PRIMARY KEY CHECK(singleton=1), recipient TEXT NOT NULL,
 calendar_id TEXT NOT NULL, version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reminder_outbox(
 id TEXT PRIMARY KEY, task_id INTEGER NOT NULL REFERENCES tasks(id),
 obligation_revision INTEGER NOT NULL, channel TEXT NOT NULL CHECK(channel IN ('email','calendar')),
 offset_days INTEGER NOT NULL, scheduled_at INTEGER NOT NULL, settings_version TEXT NOT NULL,
 payload TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN
 ('queued','inflight','accepted','created','failed','unknown','cancelled')),
 attempts INTEGER NOT NULL DEFAULT 0, provider_id TEXT, error TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS reminder_attempts(
 id INTEGER PRIMARY KEY, reminder_id TEXT NOT NULL REFERENCES reminder_outbox(id),
 started INTEGER NOT NULL, finished INTEGER, outcome TEXT NOT NULL, provider_id TEXT);
"""

def migrate(db):
    db.executescript(SCHEMA)
    with db: db.execute("INSERT OR IGNORE INTO schema_versions VALUES(4)")

def configure(db,token,recipient,calendar_id):
    user=authorize(db,token,"reminders")
    if user["role"]!="owner":
        raise PermissionError("Owner configures destinations")
    if len(recipient)>254 or recipient.count("@")!=1 or any(c.isspace() for c in recipient):
        raise ValueError("Valid email required")
    local,domain=recipient.split("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Valid email required")
    if not calendar_id.strip() or len(calendar_id)>1000:
        raise ValueError("Calendar ID required")
    version=hashlib.sha256(json.dumps([recipient,calendar_id]).encode()).hexdigest()
    with db:
        db.execute("INSERT OR REPLACE INTO reminder_settings VALUES(1,?,?,?)",
                   (recipient,calendar_id,version))
        audit(db,user,"configure-reminders","settings",{"version":version})
    return version

def task(db,task_id):
    return db.execute("""SELECT t.*,o.title,o.jurisdiction,o.owner,o.status AS applicability,
                         o.reviewed,o.revision FROM tasks t JOIN obligations o ON o.id=t.obligation_id
                         WHERE t.id=?""",(task_id,)).fetchone()

def valid(row):
    return bool(row and row["applicability"]=="applicable" and row["reviewed"]
                and row["revision"]==row["obligation_revision"] and row["due_date"]
                and not row["completed_on"])

def request_payload(channel,row,settings,key):
    subject="Compliance deadline: "+row["title"]
    text=f'{row["jurisdiction"]} · period {row["period"]} · due {row["due_date"]}. Review in Project Complied.'
    if channel=="email":
        return dict(path="/me/sendMail",body={"message":{"subject":subject,
                    "body":{"contentType":"Text","content":text},
                    "toRecipients":[{"emailAddress":{"address":settings["recipient"]}}]},
                    "saveToSentItems":True})
    due=date.fromisoformat(row["due_date"])
    return dict(path="/me/calendars/"+quote(settings["calendar_id"],safe="")+"/events",
                body={"subject":subject,"body":{"contentType":"Text","content":text},
                      "isAllDay":True,"showAs":"free",
                      "start":{"dateTime":due.isoformat()+"T00:00:00","timeZone":"Eastern Standard Time"},
                      "end":{"dateTime":(due+timedelta(days=1)).isoformat()+"T00:00:00","timeZone":"Eastern Standard Time"},
                      "transactionId":key,"isReminderOn":True,"reminderMinutesBeforeStart":1440})

def enqueue(db,token,task_id,channel,offset_days=7):
    user=authorize(db,token,"reminders")
    if channel not in ("email","calendar") or type(offset_days) is not int or not 0<=offset_days<=365:
        raise ValueError("Invalid reminder preference")
    db.execute("BEGIN IMMEDIATE")
    try:
        authorize(db,token,"reminders")
        row=task(db,task_id)
        settings=db.execute("SELECT * FROM reminder_settings WHERE singleton=1").fetchone()
        if not valid(row) or settings is None:
            raise ValueError("Verified current task and owner settings required")
        if channel=="calendar":
            offset_days=0 # one event per task/version, not one event per email reminder
        identity=[task_id,row["revision"],channel,offset_days,settings["version"]]
        key=hashlib.sha256(json.dumps(identity).encode()).hexdigest()
        due=date.fromisoformat(row["due_date"])
        send_on=due-timedelta(days=offset_days)
        scheduled=int(datetime.combine(send_on,datetime.min.time()).replace(
                      hour=9,tzinfo=ZoneInfo("America/New_York")).timestamp())
        # Calendar event can be created as soon as queued; email uses chosen date.
        if channel=="calendar":
            scheduled=int(time.time())
        payload=request_payload(channel,row,settings,key)
        cursor=db.execute("""INSERT OR IGNORE INTO reminder_outbox
            (id,task_id,obligation_revision,channel,offset_days,scheduled_at,settings_version,payload,status)
            VALUES(?,?,?,?,?,?,?,?,'queued')""",
            (key,task_id,row["revision"],channel,offset_days,scheduled,settings["version"],json.dumps(payload)))
        if cursor.rowcount:
            audit(db,user,"queue-reminder",key,{"task":task_id,"channel":channel,"offset_days":offset_days})
        db.commit()
        return key
    except Exception:
        db.rollback()
        raise

def list_outbox(db):
    settings=db.execute("SELECT version FROM reminder_settings WHERE singleton=1").fetchone()
    result=[]
    for row in db.execute("SELECT * FROM reminder_outbox ORDER BY scheduled_at,id"):
        item=dict(row)
        current=task(db,row["task_id"])
        item["needs_reconciliation"]=not valid(current) or current["revision"]!=row["obligation_revision"] or not settings or settings["version"]!=row["settings_version"]
        result.append(item)
    return result

def dispatch_one(db,transport,now=None):
    """Injected transport only; application has no configured live sender."""
    now=int(time.time()) if now is None else now
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("SELECT * FROM reminder_outbox WHERE status='queued' AND scheduled_at<=? ORDER BY scheduled_at,id LIMIT 1",(now,)).fetchone()
        if row is None:
            db.commit()
            return None
        current=task(db,row["task_id"])
        settings=db.execute("SELECT version FROM reminder_settings WHERE singleton=1").fetchone()
        if not valid(current) or current["revision"]!=row["obligation_revision"] or not settings or settings["version"]!=row["settings_version"]:
            db.execute("UPDATE reminder_outbox SET status='cancelled',error='Task or destination changed' WHERE id=?",(row["id"],))
            db.commit()
            return "cancelled"
        db.execute("UPDATE reminder_outbox SET status='inflight',attempts=attempts+1 WHERE id=?",(row["id"],))
        attempt=db.execute("INSERT INTO reminder_attempts(reminder_id,started,outcome) VALUES(?,?,'inflight')",(row["id"],now)).lastrowid
        db.commit()
    except Exception:
        db.rollback()
        raise
    try:
        outcome,provider_id=transport.send(row["channel"],json.loads(row["payload"]))
        if outcome not in ("accepted","created","failed","unknown"):
            outcome,provider_id="unknown",None
        if row["channel"]=="email" and outcome=="created":
            outcome,provider_id="unknown",None
        if row["channel"]=="calendar" and outcome=="accepted":
            outcome,provider_id="unknown",None
    except Exception:
        # Do not store exception messages that may contain credentials or HTTP bodies.
        outcome,provider_id="unknown",None
    with db:
        db.execute("UPDATE reminder_outbox SET status=?,provider_id=?,error=? WHERE id=?",
                   (outcome,provider_id,"Manual reconciliation required" if outcome=="unknown" else "",row["id"]))
        db.execute("UPDATE reminder_attempts SET finished=?,outcome=?,provider_id=? WHERE id=?",
                   (int(time.time()),outcome,provider_id,attempt))
    return outcome

def recover_inflight(db):
    """Explicit restart recovery; uncertain requests never become queued retries."""
    with db:
        db.execute("UPDATE reminder_outbox SET status='unknown',error='Interrupted attempt; reconcile before resending' WHERE status='inflight'")
        db.execute("UPDATE reminder_attempts SET outcome='unknown',finished=? WHERE outcome='inflight'",(int(time.time()),))

class MicrosoftGraphAdapter:
    """Transport accepts (path, body) and returns (HTTP status, response dict).
    OAuth and network transport must be separately provisioned; no token is persisted here."""
    def __init__(self,post):
        self.post=post
    def send(self,channel,payload):
        status,response=self.post(payload["path"],payload["body"])
        if channel=="email" and status==202:
            return "accepted",None # accepted is not delivered
        if channel=="calendar" and status==201 and response.get("id"):
            return "created",response["id"]
        if 400<=status<500 and status not in (408,429):
            return "failed",None
        return "unknown",None

def main():
    import argparse
    from complied.deadlines import connect
    parser=argparse.ArgumentParser(description="Preview reminder outbox; never sends")
    parser.add_argument("--db",default="var/demo.sqlite3")
    args=parser.parse_args()
    db=connect(args.db)
    try: print(json.dumps(list_outbox(db),indent=2))
    finally: db.close()

if __name__=="__main__":
    main()
