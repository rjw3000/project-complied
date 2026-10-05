"""Authenticated editing UI for the loopback prototype."""
import hmac
import sqlite3
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs,urlsplit
from datetime import datetime
from zoneinfo import ZoneInfo
from complied.access import authenticate,login,logout,mutate
from complied.deadlines import connect,dashboard

def page(title,content):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+escape(title)+'</title><style>'
            'body{font:16px system-ui;background:#f3f6fa;color:#192b40;margin:30px auto;max-width:1000px;padding:20px}'
            'form{background:white;border:1px solid #d9e0ea;padding:18px;margin:18px 0;border-radius:10px}'
            'label{display:block;margin:8px 0}input,select,textarea{font:inherit;padding:8px;max-width:90%}'
            'button{font:inherit;background:#174c7e;color:white;padding:10px 16px;border:0;border-radius:6px}'
            'textarea{width:90%}a{color:#174c7e}</style><h1>'+escape(title)+'</h1>'+content+'</html>')

def field(name,label,value="",kind="text"):
    return '<label>'+escape(label)+'<br><input type="'+escape(kind)+'" name="'+escape(name)+'" value="'+escape(str(value),quote=True)+'" required></label>'

def hidden(name,value):
    return '<input type="hidden" name="'+escape(name)+'" value="'+escape(str(value),quote=True)+'">'

def register_page(db,user):
    csrf=hidden("csrf",user["csrf"])
    content='<p>Local prototype · edits invalidate review and prior schedules.</p><a href="/">Dashboard</a>'
    content+='<form method="post" action="/create">'+csrf+'<h2>Add requirement</h2>'
    for name,label in [("id","Unique ID"),("title","Requirement"),("jurisdiction","Jurisdiction"),("owner","Responsible person")]:
        content+=field(name,label)
    content+='<button>Add for review</button></form>'
    for row in db.execute("SELECT * FROM obligations ORDER BY title"):
        key=hidden("id",row["id"])+hidden("revision",row["revision"])+csrf
        content+='<form method="post" action="/edit">'+key+'<h2>'+escape(row["title"])+'</h2>'
        for name,label in [("title","Requirement"),("jurisdiction","Jurisdiction"),("owner","Responsible person")]:
            content+=field(name,label,row[name])
        content+='<p>Status: '+escape(row["status"])+' · Revision '+str(row["revision"])+'</p><button>Save and require review</button></form>'
        content+='<form method="post" action="/review">'+key+'<h3>Review applicability</h3>'
        content+='<label>Decision <select name="status"><option value="applicable">Applicable</option><option value="not_applicable">Not applicable</option></select></label>'
        content+=field("source","Authority/source",row["source"])
        content+='<label>Rationale<textarea name="rationale" required>'+escape(row["rationale"])+'</textarea></label><button>Record review</button></form>'
    content+='<form method="post" action="/logout">'+csrf+'<button>Sign out</button></form>'
    return page("Requirement editing and review",content)


def reminders_page(db,user):
    from complied.reminders import list_outbox,valid,task
    csrf=hidden("csrf",user["csrf"])
    content='<p><a href="/">Dashboard</a> · <a href="/register">Requirement review</a></p>'
    content+='<p>Microsoft connection pending. Queue and preview only; nothing is sent.</p>'
    settings=db.execute("SELECT * FROM reminder_settings WHERE singleton=1").fetchone()
    if user["role"]=="owner":
        content+='<form method="post" action="/configure-reminders"><h2>Destinations</h2>'+csrf
        content+=field("recipient","Reminder email",settings["recipient"] if settings else "",kind="email")
        content+=field("calendar_id","Dedicated calendar ID",settings["calendar_id"] if settings else "")
        content+='<button>Save destinations</button></form>'
    if settings:
        content+='<form method="post" action="/queue-reminder"><h2>Queue a reminder</h2>'+csrf
        content+='<label>Verified task<select name="task_id">'
        for row in db.execute("SELECT id FROM tasks ORDER BY id"):
            record=task(db,row["id"])
            if valid(record):
                content+='<option value="'+str(row["id"])+'">'+escape(record["title"]+' · '+record["period"])+'</option>'
        content+='</select></label><label>Channel<select name="channel"><option value="email">Email</option><option value="calendar">Calendar event</option></select></label>'
        content+=field("offset_days","Days before deadline (email)",7,kind="number")
        content+='<button>Queue for preview</button></form>'
    content+='<h2>Reminder history</h2>'
    for row in list_outbox(db):
        content+='<form><strong>'+escape(row["channel"]+' · '+row["status"])+'</strong>'
        content+='<p>Task '+str(row["task_id"])+' · attempts '+str(row["attempts"])+'</p>'
        if row["needs_reconciliation"]:
            content+='<p>Task or destination changed: reconciliation needed.</p>'
        content+='<pre style="white-space:pre-wrap">'+escape(row["payload"])+'</pre></form>'
    return page("Microsoft reminders",content)


def schedules_page(db,user):
    csrf=hidden("csrf",user["csrf"])
    content='<p><a href="/">Dashboard</a> · <a href="/register">Requirement review</a></p>'
    content+='<p>Enter a reviewed schedule, preview its effect, then confirm. No statutory dates are supplied automatically.</p>'
    content+='<form method="post" action="/schedule-preview">'+csrf+'<label>Reviewed requirement<select name="obligation_id">'
    for row in db.execute("SELECT id,title FROM obligations WHERE status='applicable' AND reviewed=1 ORDER BY title"):
        content+='<option value="'+escape(row["id"],quote=True)+'">'+escape(row["title"])+'</option>'
    content+='</select></label>'
    for name,label,kind in [
        ("anchor","First month of recurrence (first day)","date"),
        ("effective_start","First eligible period month (first day)","date"),
        ("effective_end","Last eligible period month (first day)","date"),
        ("first_period","First period to preview (YYYY-MM)","month"),
        ("count","Number of periods (1–120)","number"),
        ("due_day","Day of target month (1–31)","number"),
        ("due_month_offset","Additional months after period ends (0–12)","number"),
        ("source","Authoritative source","text"),("reason","Reason for schedule approval/change","text")]:
        content+=field(name,label,kind=kind)
    content+='<label>Period length<select name="period_months"><option value="1">Monthly</option><option value="3">Quarterly</option><option value="12">Annual</option></select></label>'
    content+='<label>When day is absent from month<select name="short_month"><option value="reject">Require correction</option><option value="last_day">Use last day, if authority supports it</option></select></label>'
    content+='<label>Weekend/holiday policy<select name="roll"><option value="none">No adjustment</option><option value="next_business_day">Next business day</option></select></label>'
    content+='<label>Holiday calendar starts<input type="date" name="calendar_start"></label><label>Holiday calendar ends<input type="date" name="calendar_end"></label>'
    content+='<label>Reviewed holidays, one ISO date per line<textarea name="holidays"></textarea></label><button>Preview schedule</button></form>'
    return page("Review deadline schedules",content)

def schedule_preview_page(proposal,preview,user):
    content='<p>Review each change. This preview expires in 15 minutes. Confirmation applies the entire batch.</p><table><tr><th>Period</th><th>Old deadline</th><th>Proposed deadline</th><th>Action</th></tr>'
    for row in preview["rows"]:
        old=(row["before"] or {}).get("due_date") or "None"
        content+='<tr>'+''.join('<td>'+escape(str(value))+'</td>' for value in [row["period"],old,row["due_date"],row["action"]])+'</tr>'
    content+='</table><p>Completed tasks and unresolved external operations cannot be overwritten. Queued stale reminders will be cancelled; sent messages remain in history.</p>'
    if not any(row["action"].startswith("blocked") for row in preview["rows"]):
        content+='<form method="post" action="/schedule-confirm">'+hidden("csrf",user["csrf"])+hidden("proposal_id",proposal)+'<button>Confirm reviewed schedule</button></form>'
    content+='<a href="/schedules">Back to schedules</a>'
    return page("Confirm schedule changes",content)


def preparation_page(db):
    import json
    content='<p><a href="/">Dashboard</a></p><p>Normalized synthetic source packages. Actual PostalMate column mapping and tax treatment remain unverified. These are not submission-ready returns.</p>'
    for row in db.execute("SELECT * FROM preparation_packages ORDER BY period DESC,id"):
        manifest=json.loads(row["manifest"])
        content+='<form><h2>'+escape(manifest["period"])+'</h2><p>Package '+escape(row["id"])+'</p>'
        content+='<p>Status: source reconciled; return preparation pending.</p><table><tr><th>Store</th><th>Taxable net sales</th><th>Nontaxable net sales</th><th>Tax collected</th></tr>'
        for source in manifest["sources"]:
            content+='<tr>'+''.join('<td>'+escape(str(source[key]))+'</td>' for key in ["store_id","net_taxable_sales","net_nontaxable_sales","tax_collected"])+'</tr>'
        content+='</table><p>Combined net sales: '+escape(manifest["totals"]["net_sales_control"])+' · Tax collected: '+escape(manifest["totals"]["tax_collected"])+'</p>'
        content+='<details><summary>Source hashes and contract</summary><pre style="white-space:pre-wrap">'+escape(json.dumps(manifest,indent=2))+'</pre></details></form>'
    return page("Monthly sales preparation",content)

def handler_for(db_path):
    class Handler(BaseHTTPRequestHandler):
        def origin(self):
            return "http://127.0.0.1:"+str(self.server.server_port)
        def allowed_host(self):
            return self.headers.get("Host")=="127.0.0.1:"+str(self.server.server_port)
        def token(self):
            cookies=SimpleCookie()
            try:
                cookies.load(self.headers.get("Cookie",""))
                return cookies["complied_session"].value if "complied_session" in cookies else ""
            except Exception:
                return ""
        def respond(self,status,content,cookie=None):
            payload=content.encode()
            self.send_response(status)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(payload)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            if cookie: self.send_header("Set-Cookie",cookie)
            self.end_headers()
            self.wfile.write(payload)
        def redirect(self,target,cookie=None):
            self.send_response(303)
            self.send_header("Location",target)
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length","0")
            if cookie: self.send_header("Set-Cookie",cookie)
            self.end_headers()
        def do_GET(self):
            if not self.allowed_host():
                self.send_error(403)
                return
            path=urlsplit(self.path).path
            if path=="/login":
                form='<form method="post" action="/login">'+field("user","User")+field("password","Password",kind="password")+'<button>Sign in</button></form>'
                self.respond(200,page("Project Complied sign-in",form))
                return
            if path not in ("/","/register","/reminders","/schedules","/preparation"):
                self.send_error(404)
                return
            db=connect(db_path)
            try:
                user=authenticate(db,self.token())
                if path=="/preparation":
                    content=preparation_page(db)
                elif path=="/schedules":
                    content=schedules_page(db,user)
                elif path=="/reminders":
                    content=reminders_page(db,user)
                elif path=="/register":
                    content=register_page(db,user)
                else:
                    from complied.web import render
                    today=datetime.now(ZoneInfo("America/New_York")).date()
                    content=render(dashboard(db,today),today).replace("<header>","<header><p><a href='/register'>Edit and review requirements</a> · <a href='/reminders'>Microsoft reminders</a> · <a href='/schedules'>Review schedules</a> · <a href='/preparation'>Sales preparation</a></p>",1)
                self.respond(200,content)
            except PermissionError:
                self.redirect("/login")
            finally:
                db.close()
        def do_POST(self):
            if not self.allowed_host() or self.headers.get("Origin")!=self.origin():
                self.send_error(403)
                return
            path=urlsplit(self.path).path
            if path not in ("/login","/logout","/create","/edit","/review","/configure-reminders","/queue-reminder","/schedule-preview","/schedule-confirm"):
                self.send_error(404)
                return
            try:
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=16384 or self.headers.get("Content-Type","").split(";")[0]!="application/x-www-form-urlencoded":
                    self.send_error(400)
                    return
                values=parse_qs(self.rfile.read(length).decode("utf-8"),keep_blank_values=True,max_num_fields=24)
                if any(len(v)!=1 for v in values.values()):
                    raise ValueError("Duplicate form fields")
                fields={k:v[0] for k,v in values.items()}
            except (ValueError,UnicodeError):
                self.send_error(400)
                return
            db=connect(db_path)
            try:
                if path=="/login":
                    token,_=login(db,fields["user"],fields["password"])
                    self.redirect("/",f"complied_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600")
                    return
                token=self.token()
                user=authenticate(db,token)
                if not hmac.compare_digest(user["csrf"],fields.get("csrf","")):
                    raise PermissionError("Invalid request token")
                if path=="/logout":
                    logout(db,token)
                    self.redirect("/login","complied_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
                elif path=="/schedule-preview":
                    from complied.schedules import propose
                    definition={key:fields[key] for key in ("anchor","effective_start","effective_end","short_month","roll")}
                    for key in ("period_months","due_month_offset","due_day"):
                        definition[key]=int(fields[key])
                    definition["calendar_start"]=fields.get("calendar_start") or None
                    definition["calendar_end"]=fields.get("calendar_end") or None
                    definition["holidays"]=[line.strip() for line in fields.get("holidays","").splitlines() if line.strip()]
                    proposal,preview=propose(db,token,fields["obligation_id"],definition,fields["source"],
                                             fields["first_period"],int(fields["count"]),fields["reason"])
                    self.respond(200,schedule_preview_page(proposal,preview,user))
                elif path=="/schedule-confirm":
                    from complied.schedules import confirm
                    confirm(db,token,fields["proposal_id"])
                    self.redirect("/")
                elif path=="/configure-reminders":
                    from complied.reminders import configure
                    configure(db,token,fields["recipient"],fields["calendar_id"])
                    self.redirect("/reminders")
                elif path=="/queue-reminder":
                    from complied.reminders import enqueue
                    enqueue(db,token,int(fields["task_id"]),fields["channel"],int(fields["offset_days"]))
                    self.redirect("/reminders")
                else:
                    mutate(db,token,path[1:],fields)
                    self.redirect("/register")
            except PermissionError:
                self.respond(403,page("Request denied","<p>Sign in again or reload the form.</p>"))
            except (ValueError,KeyError,sqlite3.IntegrityError):
                self.respond(409,page("Change not saved","<p>Check required fields and reload the record before retrying.</p><a href='/register'>Return to register</a>"))
            finally:
                db.close()
    return Handler
