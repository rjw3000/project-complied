"""Local account/session and reviewed editing service. Prototype only."""
import argparse
import getpass
import hashlib
import hmac
import json
import secrets
import time
from datetime import date

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY, role TEXT NOT NULL CHECK(role IN ('owner','delegate')),
 salt TEXT NOT NULL, password_hash TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
 failures INTEGER NOT NULL DEFAULT 0, locked_until INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS sessions(
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 csrf TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events(
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL REFERENCES users(id),
 action TEXT NOT NULL, object_id TEXT NOT NULL, created INTEGER NOT NULL,
 details TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_events
 BEGIN SELECT RAISE(ABORT,'Audit is append only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_events
 BEGIN SELECT RAISE(ABORT,'Audit is append only'); END;
"""

def migrate(db):
    db.executescript(SCHEMA)
    with db:
        for table,column in [("obligations","revision"),("tasks","obligation_revision"),
                             ("deadline_rules","obligation_revision")]:
            columns={row["name"] for row in db.execute("PRAGMA table_info("+table+")")}
            if column not in columns:
                db.execute("ALTER TABLE "+table+" ADD COLUMN "+column+" INTEGER NOT NULL DEFAULT 0")
        db.execute("INSERT OR IGNORE INTO schema_versions VALUES(3)")

def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),
                          n=16384,r=8,p=1,maxmem=67108864).hex()

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def create_user(db,user_id,role,password):
    if role not in ("owner","delegate") or not user_id.strip() or len(user_id)>100:
        raise ValueError("Invalid account")
    if not 12 <= len(password) <= 256:
        raise ValueError("Password must have 12..256 characters")
    salt=secrets.token_hex(16)
    with db:
        db.execute("INSERT INTO users(id,role,salt,password_hash) VALUES(?,?,?,?)",
                   (user_id,role,salt,password_hash(password,salt)))

def login(db,user_id,password,now=None):
    now=int(time.time()) if now is None else now
    if not isinstance(password,str) or len(password)>256:
        raise PermissionError("Sign-in failed")
    user=db.execute("SELECT * FROM users WHERE id=?",(user_id,)).fetchone()
    salt=user["salt"] if user else "00"*16
    valid=hmac.compare_digest(password_hash(password,salt),
                              user["password_hash"] if user else "00"*64)
    if user is None or not user["enabled"] or user["locked_until"]>now or not valid:
        if user and not valid:
            with db:
                failures=user["failures"]+1
                db.execute("UPDATE users SET failures=?,locked_until=? WHERE id=?",
                           (failures,now+300 if failures>=5 else 0,user_id))
        raise PermissionError("Sign-in failed")
    token=secrets.token_urlsafe(32)
    csrf=secrets.token_urlsafe(32)
    with db:
        db.execute("UPDATE users SET failures=0,locked_until=0 WHERE id=?",(user_id,))
        db.execute("INSERT INTO sessions VALUES(?,?,?,?)",(digest(token),user_id,csrf,now+3600))
    return token,csrf

def authenticate(db,token,now=None):
    now=int(time.time()) if now is None else now
    user=db.execute("""SELECT u.id,u.role,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id
                       WHERE s.token_hash=? AND s.expires>? AND u.enabled=1""",
                    (digest(token),now)).fetchone()
    if user is None:
        raise PermissionError("Sign-in required")
    return dict(user)

def authorize(db,token,action,now=None):
    user=authenticate(db,token,now)
    allowed={"create","edit","review","reminders"}
    if action not in allowed and not (action=="initiate_payment" and user["role"]=="owner"):
        raise PermissionError("Action not permitted")
    return user

def logout(db,token):
    with db: db.execute("DELETE FROM sessions WHERE token_hash=?",(digest(token),))

def disable_user(db,user_id):
    # Administrative CLI operation only; no public user-management endpoint.
    with db:
        db.execute("UPDATE users SET enabled=0 WHERE id=?",(user_id,))
        db.execute("DELETE FROM sessions WHERE user_id=?",(user_id,))

def audit(db,user,action,object_id,details):
    db.execute("INSERT INTO audit_events(actor,action,object_id,created,details) VALUES(?,?,?,?,?)",
               (user["id"],action,object_id,int(time.time()),json.dumps(details,sort_keys=True)))

def mutate(db,token,action,fields):
    user=authorize(db,token,action)
    if action not in ("create","edit","review"):
        raise ValueError("Unsupported mutation")
    db.execute("BEGIN IMMEDIATE")
    try:
        # Recheck session/role under the write transaction.
        user=authorize(db,token,action)
        object_id=fields["id"].strip()
        if not object_id or len(object_id)>100:
            raise ValueError("ID required")
        if action=="create":
            for key in ("title","jurisdiction","owner"):
                if not fields.get(key,"").strip() or len(fields[key])>500:
                    raise ValueError("Title, jurisdiction and owner required")
            db.execute("""INSERT INTO obligations(id,title,jurisdiction,status,source,rationale,owner,
                          location_id,reviewed,revision) VALUES(?,?,?,'unresolved','','',?,NULL,0,0)""",
                       (object_id,fields["title"],fields["jurisdiction"],fields["owner"]))
            revision=0
        else:
            row=db.execute("SELECT * FROM obligations WHERE id=?",(object_id,)).fetchone()
            if row is None or row["revision"]!=int(fields["revision"]):
                raise ValueError("Record changed; reload before saving")
            revision=row["revision"]+1
            if action=="edit":
                for key in ("title","jurisdiction","owner"):
                    if not fields.get(key,"").strip() or len(fields[key])>500:
                        raise ValueError("Title, jurisdiction and owner required")
                db.execute("""UPDATE obligations SET title=?,jurisdiction=?,owner=?,status='unresolved',
                              reviewed=0,revision=? WHERE id=?""",
                           (fields["title"],fields["jurisdiction"],fields["owner"],revision,object_id))
            else:
                status=fields.get("status")
                source=fields.get("source","").strip()
                rationale=fields.get("rationale","").strip()
                if status not in ("applicable","not_applicable") or not source or not rationale:
                    raise ValueError("Review needs status, source and rationale")
                if len(source)>2000 or len(rationale)>4000:
                    raise ValueError("Review text too long")
                db.execute("""UPDATE obligations SET status=?,source=?,rationale=?,reviewed=1,
                              revision=? WHERE id=?""",(status,source,rationale,revision,object_id))
        audit(db,user,action,object_id,{"revision":revision,"fields":{k:v for k,v in fields.items() if k in {"id","title","jurisdiction","owner","revision","status","source","rationale"}}})
        db.commit()
        return revision
    except Exception:
        db.rollback()
        raise

def main():
    from pathlib import Path
    from complied.deadlines import connect
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["create-user","disable-user"])
    parser.add_argument("--user",required=True)
    parser.add_argument("--role",choices=["owner","delegate"],default="owner")
    parser.add_argument("--db",default="var/demo.sqlite3")
    args=parser.parse_args()
    Path(args.db).parent.mkdir(parents=True,exist_ok=True)
    db=connect(args.db)
    try:
        if args.command=="create-user":
            password=getpass.getpass("New local password (12+ characters): ")
            if password!=getpass.getpass("Confirm password: "):
                raise ValueError("Passwords differ")
            create_user(db,args.user,args.role,password)
        else:
            disable_user(db,args.user)
    finally:
        db.close()

if __name__=="__main__":
    main()
