"""Tenant-scoped Microsoft web sign-in and encrypted delegated Graph cache."""
import json
import os
import re
import secrets
import time
from urllib.parse import urlsplit
from cryptography.fernet import Fernet
import msal
from complied.access import authenticate,create_user,start_session,digest

GRAPH_SCOPES=["Mail.Send","Calendars.ReadWrite"]
GUID=re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")

def configured():
    return os.environ.get("COMPLIED_AUTH_MODE","local")=="microsoft"

def settings():
    names=("COMPLIED_PUBLIC_ORIGIN","COMPLIED_TENANT_ID","COMPLIED_CLIENT_ID",
           "COMPLIED_CLIENT_SECRET","COMPLIED_OWNER_OID","COMPLIED_TOKEN_KEY")
    data={key:os.environ.get(key,"") for key in names}
    origin=urlsplit(data["COMPLIED_PUBLIC_ORIGIN"])
    if (not all(data.values()) or origin.scheme!="https" or not origin.hostname or
        origin.path or origin.query or origin.fragment or origin.username or origin.password or
        any(not GUID.fullmatch(data[key]) for key in
            ("COMPLIED_TENANT_ID","COMPLIED_CLIENT_ID","COMPLIED_OWNER_OID"))):
        raise ValueError("Microsoft deployment configuration is incomplete")
    try:
        Fernet(data["COMPLIED_TOKEN_KEY"].encode())
    except Exception as exc:
        raise ValueError("Invalid token encryption key") from exc
    return data

def role_for(oid):
    owner=os.environ.get("COMPLIED_OWNER_OID","").lower()
    delegates={part.strip().lower() for part in os.environ.get("COMPLIED_DELEGATE_OIDS","").split(",") if part.strip()}
    if isinstance(oid,str) and GUID.fullmatch(oid) and oid.lower()==owner:
        return "owner"
    if isinstance(oid,str) and GUID.fullmatch(oid) and oid.lower() in delegates:
        return "delegate"
    return None

def migrate(db):
    db.executescript("""
      CREATE TABLE IF NOT EXISTS microsoft_flows(
        browser_hash TEXT PRIMARY KEY,kind TEXT NOT NULL CHECK(kind IN ('login','connect')),
        session_hash TEXT NOT NULL,flow TEXT NOT NULL,expires INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS microsoft_connections(
        user_id TEXT PRIMARY KEY REFERENCES users(id),encrypted_cache BLOB NOT NULL,
        connected_at INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS microsoft_runtime_status(
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),status TEXT NOT NULL,updated INTEGER NOT NULL);
    """)
    with db: db.execute("INSERT OR IGNORE INTO schema_versions VALUES(8)")

def app(config,cache=None):
    return msal.ConfidentialClientApplication(
        config["COMPLIED_CLIENT_ID"],
        authority="https://login.microsoftonline.com/"+config["COMPLIED_TENANT_ID"],
        client_credential=config["COMPLIED_CLIENT_SECRET"],token_cache=cache)

def begin(db,kind,session=""):
    config=settings()
    if kind not in ("login","connect"):
        raise ValueError("Invalid Microsoft flow")
    if kind=="connect" and authenticate(db,session)["role"]!="owner":
        raise PermissionError("Only the owner can connect reminders")
    flow=app(config).initiate_auth_code_flow(
        scopes=GRAPH_SCOPES if kind=="connect" else ["User.Read"],
        redirect_uri=config["COMPLIED_PUBLIC_ORIGIN"]+"/auth/callback",response_mode="query")
    url=flow.get("auth_uri","")
    if (not url.startswith("https://login.microsoftonline.com/") or
        any(ch in url for ch in "\r\n") or not flow.get("state")):
        raise ValueError("Microsoft authorization unavailable")
    browser=secrets.token_urlsafe(32)
    with db:
        db.execute("DELETE FROM microsoft_flows WHERE expires<?",(int(time.time()),))
        db.execute("INSERT INTO microsoft_flows VALUES(?,?,?,?,?)",
                   (digest(browser),kind,digest(session) if session else "",
                    json.dumps(flow),int(time.time())+600))
    return url,browser

def finish(db,browser,params,session=""):
    config=settings()
    if not browser or len(browser)>256:
        raise PermissionError("Authorization session missing")
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("SELECT * FROM microsoft_flows WHERE browser_hash=?",(digest(browser),)).fetchone()
        if row is None or row["expires"]<int(time.time()) or (
            row["kind"]=="connect" and
            (row["session_hash"]!=digest(session) or authenticate(db,session)["role"]!="owner")):
            raise PermissionError("Authorization session expired")
        db.execute("DELETE FROM microsoft_flows WHERE browser_hash=?",(row["browser_hash"],))
        db.commit()
    except Exception:
        db.rollback()
        raise
    flow=json.loads(row["flow"])
    if params.get("state")!=flow["state"] or not params.get("code"):
        raise PermissionError("Invalid Microsoft response")
    cache=msal.SerializableTokenCache()
    try:
        result=app(config,cache).acquire_token_by_auth_code_flow(flow,params)
    except (ValueError,KeyError) as exc:
        raise PermissionError("Microsoft sign-in failed") from exc
    claims=result.get("id_token_claims",{})
    oid=claims.get("oid","")
    if (claims.get("tid","").lower()!=config["COMPLIED_TENANT_ID"].lower() or
        not GUID.fullmatch(oid) or not result.get("access_token")):
        raise PermissionError("Microsoft identity not verified")
    role=role_for(oid)
    if role is None:
        raise PermissionError("Account is not authorized for this tool")
    user_id="ms:"+oid.lower()
    if row["kind"]=="login":
        existing=db.execute("SELECT id,enabled FROM users WHERE id=?",(user_id,)).fetchone()
        if existing is None:
            create_user(db,user_id,role,secrets.token_urlsafe(48))
        elif not existing["enabled"]:
            raise PermissionError("Account disabled")
        with db: db.execute("UPDATE users SET role=? WHERE id=?",(role,user_id))
        return start_session(db,user_id),"login"
    if role!="owner" or authenticate(db,session)["id"]!=user_id:
        raise PermissionError("Microsoft account does not match signed-in owner")
    db.execute("BEGIN IMMEDIATE")
    try:
        if authenticate(db,session)["id"]!=user_id:
            raise PermissionError("Owner session changed")
        db.execute("INSERT OR REPLACE INTO microsoft_connections VALUES(?,?,?)",
                   (user_id,Fernet(config["COMPLIED_TOKEN_KEY"].encode()).encrypt(cache.serialize().encode()),
                    int(time.time())))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return None,"connect"

def connected(db,user_id):
    return db.execute("SELECT 1 FROM microsoft_connections WHERE user_id=?",(user_id,)).fetchone() is not None

def disconnect(db,session):
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authenticate(db,session)
        if user["role"]!="owner":
            raise PermissionError("Only owner can disconnect")
        db.execute("DELETE FROM microsoft_connections WHERE user_id=?",(user["id"],))
        db.commit()
    except Exception:
        db.rollback()
        raise

def graph_token(db,user_id):
    config=settings()
    if user_id!="ms:"+config["COMPLIED_OWNER_OID"].lower() or role_for(config["COMPLIED_OWNER_OID"])!="owner":
        raise PermissionError("Owner connection required")
    owner=db.execute("SELECT enabled,role FROM users WHERE id=?",(user_id,)).fetchone()
    if owner is None or not owner["enabled"] or owner["role"]!="owner":
        raise PermissionError("Owner account unavailable")
    row=db.execute("SELECT encrypted_cache FROM microsoft_connections WHERE user_id=?",(user_id,)).fetchone()
    if row is None:
        raise PermissionError("Connect Microsoft reminders first")
    cache=msal.SerializableTokenCache()
    cache.deserialize(Fernet(config["COMPLIED_TOKEN_KEY"].encode()).decrypt(row["encrypted_cache"]).decode())
    client=app(config,cache)
    accounts=client.get_accounts()
    if len(accounts)!=1:
        raise PermissionError("Reconnect Microsoft reminders")
    result=client.acquire_token_silent(GRAPH_SCOPES,account=accounts[0])
    db.execute("BEGIN IMMEDIATE")
    try:
        if not connected(db,user_id) or not db.execute("SELECT enabled FROM users WHERE id=?",(user_id,)).fetchone()["enabled"]:
            raise PermissionError("Microsoft connection removed")
        if cache.has_state_changed:
            db.execute("UPDATE microsoft_connections SET encrypted_cache=? WHERE user_id=?",
                       (Fernet(config["COMPLIED_TOKEN_KEY"].encode()).encrypt(cache.serialize().encode()),user_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    if not result or not result.get("access_token"):
        raise PermissionError("Reconnect Microsoft reminders")
    return result["access_token"]
