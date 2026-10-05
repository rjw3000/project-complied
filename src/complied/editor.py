"""Authenticated editing UI for the loopback prototype."""
import hmac
import os
import sqlite3
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs,urlsplit
from datetime import datetime
from zoneinfo import ZoneInfo
from complied.access import authenticate,login,logout,mutate
from complied.deadlines import connect,dashboard

def page(title,content,public=False):
    nav=('<nav aria-label="Main navigation"><a href="/">Overview</a>'
         '<a href="/register">Requirements</a><a href="/schedules">Schedules</a>'
         '<a href="/preparation">Sales preparation</a><a href="/reminders">Reminders</a></nav>')
    header=('<header class="topbar"><a class="brand" href="/">◆ <span>PROJECT COMPLIED</span></a>'
            +('' if public else nav)+
            '<span class="environment">Internal prototype</span></header>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+escape(title)+' · Project Complied</title>'
            '<style>'
            ':root{color-scheme:light;--ink:#172b41;--muted:#50657b;--line:#dbe5ed;--bg:#f3f7f9;--blue:#174c7e}'
            '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,sans-serif}'
            'a{color:var(--blue);text-underline-offset:3px}.topbar{display:flex;align-items:center;gap:24px;padding:16px max(24px,calc((100vw - 1180px)/2));background:#102b43;color:#fff;flex-wrap:wrap}'
            '.brand{font-weight:800;letter-spacing:.07em;text-decoration:none;color:white;white-space:nowrap}.brand:first-letter{color:#77d6bc}'
            'nav{display:flex;gap:18px;flex-wrap:wrap}nav a{color:#e4eef6;text-decoration:none;font-size:14px}nav a:hover,nav a:focus-visible{text-decoration:underline}'
            '.environment{margin-left:auto;border:1px solid #6591a1;border-radius:99px;padding:3px 11px;color:#c5dfec;font-size:12px}'
            'main{max-width:1180px;margin:auto;padding:36px 24px 72px}h1{font-size:clamp(28px,4vw,40px);letter-spacing:-.035em;line-height:1.16;margin:0 0 12px}'
            'h2{font-size:22px;margin:0 0 10px}h3{margin:0 0 10px}p{margin:10px 0 16px}small,.muted{color:var(--muted)}'
            'form,.panel,.card,.table{background:white;border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 20px rgba(17,47,71,.04)}'
            'form,.panel{padding:22px;margin:20px 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:24px 0}'
            '.card{padding:19px}.card strong{display:block;font-size:30px;line-height:1.2}.card span{color:var(--muted);font-size:14px}'
            '.notice{padding:16px 20px;border:1px solid #e6c987;background:#fff6df;border-radius:12px}.table{overflow:auto}'
            'table{border-collapse:collapse;width:100%;text-align:left}th,td{padding:13px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#eaf0f5;font-size:13px;white-space:nowrap}tr:last-child td{border-bottom:0}'
            'label{display:block;margin:12px 0;color:#344c63;font-weight:600}input,select,textarea{display:block;width:min(100%,680px);font:inherit;padding:10px 12px;border:1px solid #aabccc;border-radius:7px;background:white;color:var(--ink)}'
            'input:focus,select:focus,textarea:focus,button:focus-visible,a:focus-visible{outline:3px solid #54a9db;outline-offset:2px}'
            'input[type=hidden]{display:none}textarea{min-height:95px}button{font:inherit;font-weight:650;background:var(--blue);color:white;padding:10px 17px;border:0;border-radius:7px;cursor:pointer}'
            'button:hover{background:#0e395f}.button-link{display:inline-block;background:#174c7e;color:white;text-decoration:none;padding:10px 17px;border-radius:7px;font-weight:650}'
            '.steps{list-style:none;display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:0;margin:24px 0}.steps li{padding:12px;background:#e6edf2;border-radius:10px;color:#385269;font-weight:650}.steps .current{background:#174c7e;color:white}'
            '.action-card{background:#e7f5f1;border:1px solid #9dd0bf;border-radius:14px;padding:23px;margin:22px 0}.badge{font-size:12px;font-weight:700;display:inline-block;padding:3px 9px;border-radius:99px;background:#e6eef4;color:#174c7e;vertical-align:middle}'
            '.checks{list-style:none;padding:0}.checks li{border-bottom:1px solid var(--line);padding:12px 0}.checks li:last-child{border:0}.checks p{color:var(--muted);margin:4px 0}'
            'pre{overflow:auto;padding:14px;background:#f0f4f8;border-radius:8px}details{margin:16px 0}'
            '@media(max-width:640px){.topbar{gap:12px;padding:16px 20px}.environment{margin-left:0}main{padding:28px 18px 54px}form,.panel{padding:17px}th,td{padding:10px;font-size:14px}}'
            '</style></head><body>'+header+'<main><h1>'+escape(title)+'</h1>'+content+'</main></body></html>')


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
    from complied.microsoft_identity import configured,connected
    live=configured()
    linked=connected(db,user["id"]) if live and user["role"]=="owner" else False
    if live:
        content+='<p>Live delivery is '+("configured" if linked else "awaiting owner connection")+'. Queued work is sent only when the separate worker is enabled.</p>'
        if user["role"]=="owner":
            if linked:
                content+='<p><a href="/microsoft-calendars">Browse Microsoft calendars</a></p>'
                content+='<form method="post" action="/disconnect-microsoft">'+csrf+'<button>Disconnect Microsoft reminders</button></form>'
            else:
                content+='<form method="post" action="/connect-microsoft">'+csrf+'<button>Connect Microsoft reminders</button></form>'
    else:
        content+='<p>Microsoft connection pending. Queue and preview only; nothing is sent.</p>'
    settings=db.execute("SELECT * FROM reminder_settings WHERE singleton=1").fetchone()
    if user["role"]=="owner" and (not live or linked):
        content+='<form method="post" action="/configure-reminders"><h2>Destinations</h2>'+csrf
        content+=field("recipient","Reminder email",settings["recipient"] if settings else "",kind="email")
        content+=field("calendar_id","Dedicated calendar ID",settings["calendar_id"] if settings else "")
        content+='<button>Save destinations</button></form>'
    if settings and (not live or connected(db,"ms:"+os.environ.get("COMPLIED_OWNER_OID","").lower())):
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


def calendars_page(db,user,token):
    from complied.microsoft_identity import graph_token
    from complied.microsoft import GraphHTTPTransport
    if user["role"]!="owner":
        raise PermissionError("Owner calendar selection required")
    graph=GraphHTTPTransport(graph_token(db,user["id"]),enabled=True)
    calendars=graph.get_calendars()
    settings=db.execute("SELECT recipient FROM reminder_settings WHERE singleton=1").fetchone()
    content='<p>Choose a dedicated calendar for deadline events. The recipient receives reminder email.</p>'
    content+='<form method="post" action="/configure-reminders">'+hidden("csrf",user["csrf"])
    content+=field("recipient","Reminder email",settings["recipient"] if settings else "",kind="email")
    content+='<label>Microsoft calendar<select name="calendar_id" required>'
    for calendar in calendars:
        content+='<option value="'+escape(calendar["id"],quote=True)+'">'+escape(calendar["name"])+'</option>'
    content+='</select></label><button>Save calendar and recipient</button></form>'
    content+='<a href="/reminders">Back to reminders</a>'
    return page("Select Microsoft calendar",content)


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


def steps(active):
    names=(("upload","1 · Upload"),("reconcile","2 · Reconcile"),("review","3 · Review"))
    return '<ol class="steps" aria-label="Monthly workflow">'+''.join(
        '<li'+(' class="current" aria-current="step"' if name==active else '')+'>'+label+'</li>'
        for name,label in names)+'</ol>'

def preparation_page(db,user):
    from complied.workflow import months
    items=months(db)
    content='<p class="muted">One legal entity · Ivy Road and Pantops · source review for each month.</p>'
    active="upload" if not items else ("review" if items[0]["review_state"]=="sources_reviewed" else "reconcile")
    content+=steps(active)
    if items:
        first=items[0]
        content+='<section class="action-card"><h2>Next action · '+escape(first["manifest"]["period"])+'</h2>'
        content+='<p>'+escape(first["next_action"])+'</p><a class="button-link" href="'+escape(first["next_href"],quote=True)+'">Continue monthly workflow</a></section>'
    else:
        content+='<section class="action-card"><h2>Start a monthly package</h2><p>Upload one normalized CSV from each store for the same month.</p><a href="#upload">Go to upload</a></section>'
    content+='<form id="upload" method="post" action="/upload-sales" enctype="multipart/form-data">'
    content+=hidden("csrf",user["csrf"])
    content+='<h2>Upload store reports</h2><p>Use the normalized monthly CSV contract. Actual PostalMate report columns still need a reviewed mapping. Each file is limited to 64 KiB.</p>'
    content+='<label>Ivy Road CSV<input type="file" name="ivy" accept=".csv,text/csv" required></label>'
    content+='<label>Pantops CSV<input type="file" name="pantops" accept=".csv,text/csv" required></label>'
    content+='<button>Validate both stores</button></form>'
    if not items:
        content+='<section class="panel"><h2>No packages yet</h2><p>Once both reports pass validation, this page will show the reconciliation and review actions.</p></section>'
    for item in items:
        manifest=item["manifest"]
        period=escape(manifest["period"])
        key=item["package_id"]
        label={"needs_review":"Source review needed","sources_reviewed":"Source totals reviewed",
               "needs_information":"Needs information","rejected":"Rejected"}[item["review_state"]]
        content+='<section class="panel"><h2>'+period+' <span class="badge">'+escape(label)+'</span></h2>'
        content+='<p>Combined net sales '+escape(manifest["totals"]["net_sales_control"])+' · Tax collected '+escape(manifest["totals"]["tax_collected"])+'</p>'
        content+='<p>'+escape(item["next_action"])+'</p><p><a href="/reconcile?id='+key+'">Inspect reconciliation</a> · <a href="/package?id='+key+'">Review source package</a></p>'
        content+='<small>Source package '+key[:12]+'… · Return preparation pending</small>'
        older=[row["id"] for row in db.execute("SELECT id FROM preparation_packages WHERE period=?",(manifest["period"],)) if row["id"]!=key]
        if older:
            content+='<details><summary>Earlier packages for this month ('+str(len(older))+')</summary><ul>'
            content+=''.join('<li><a href="/reconcile?id='+old+'">'+old[:12]+'…</a></li>' for old in older)
            content+='</ul></details>'
        content+='</section>'
    content+='<p class="notice">Passing source controls does not establish a tax amount or a submission-ready return. Filing and payment remain separate.</p>'
    return page("Monthly sales preparation",content)

def reconcile_page(db,package_id):
    from complied.workflow import assess
    data=assess(db,package_id)
    manifest=data["manifest"]
    content='<p><a href="/preparation">Monthly packages</a> · '+escape(manifest["period"])+'</p>'
    content+=steps("reconcile")
    content+='<p>Compare the two store controls with the combined entity total. These checks revalidate the stored CSV bytes and arithmetic.</p>'
    content+='<div class="table"><table><caption>Selected store totals</caption><thead><tr><th>Store</th><th>Taxable net</th><th>Nontaxable net</th><th>Net sales control</th><th>Tax collected</th></tr></thead><tbody>'
    for source in manifest["sources"]:
        content+='<tr>'+''.join('<td>'+escape(str(source[field]))+'</td>' for field in
            ("store_id","net_taxable_sales","net_nontaxable_sales","net_sales_control","tax_collected"))+'</tr>'
    content+='<tr><th>Combined LLC</th>'+''.join('<td>'+escape(manifest["totals"][field])+'</td>' for field in
        ("net_taxable_sales","net_nontaxable_sales","net_sales_control","tax_collected"))+'</tr></tbody></table></div>'
    content+='<section class="panel"><h2>Reconciliation checks</h2><ul class="checks">'
    for check in data["checks"]:
        content+='<li><strong>'+escape(check["label"])+'</strong> <span class="badge">'+escape(check["state"])+'</span><p>'+escape(check["detail"])+'</p></li>'
    content+='</ul></section>'
    if data["alternatives"]:
        content+='<details><summary>Other imported versions for this month</summary><ul>'
        content+=''.join('<li>'+escape(key)+'</li>' for key in data["alternatives"])
        content+='</ul><p>Compare these versions and document which reports were selected in the review notes.</p></details>'
    content+='<details><summary>Selected snapshot hashes</summary><ul>'
    content+=''.join('<li>'+escape(source["store_id"])+': '+escape(source["snapshot_id"])+'</li>' for source in manifest["sources"])
    content+='</ul></details>'
    content+='<section class="action-card"><h2>Next: source review</h2><p>Record whether these source totals can be accepted, need more information or should be rejected.</p><a class="button-link" href="/package?id='+package_id+'">Continue to review</a></section>'
    content+='<p class="notice">Tax classifications and government return lines remain unverified; this package is not ready to file.</p>'
    return page("Reconcile monthly sales",content)

def package_page(db,user,package_id):
    from complied.workflow import assess
    from complied.package_review import context
    data=assess(db,package_id)
    context_hash,_=context(db,data["manifest"])
    content='<p><a href="/preparation">Monthly packages</a> · <a href="/reconcile?id='+package_id+'">Reconciliation</a></p>'
    content+=steps("review")
    content+='<p>Period '+escape(data["manifest"]["period"])+' · Source status: <strong>'+escape(data["review_state"].replace("_"," "))+'</strong>.</p>'
    content+='<p>Selected net sales: '+escape(data["manifest"]["totals"]["net_sales_control"])+' · Tax collected: '+escape(data["manifest"]["totals"]["tax_collected"])+'</p>'
    content+='<section class="panel"><h2>Next action</h2><p>'+escape(data["next_action"])+'</p></section>'
    content+='<section class="panel"><h2>Open blockers</h2><ul>'+''.join('<li>'+escape(blocker)+'</li>' for blocker in data["blockers"])+'</ul></section>'
    content+='<p>Compare each selected snapshot hash and any other imported version before deciding. <a href="/reconcile?id='+package_id+'">See detailed totals and checks</a>.</p>'
    content+='<form method="post" action="/package-review"><h2>Record source decision</h2>'
    content+=hidden("csrf",user["csrf"])+hidden("package_id",package_id)+hidden("revision",data["review_revision"])+hidden("context",context_hash)
    content+='<label>Source decision<select name="decision"><option value="sources_reviewed">Source totals reviewed</option><option value="needs_information">Needs information</option><option value="rejected">Reject source package</option></select></label>'
    content+='<label>Review notes<textarea name="notes" required maxlength="4000" placeholder="Explain the selected store reports, any differences and next action."></textarea></label><button>Record source review</button></form>'
    content+='<p>Source review does not authorize government submission or payment. <a href="/package-export?id='+package_id+'">Download source review packet</a>.</p>'
    content+='<h2>Review history</h2>'
    if not data["reviews"]:
        content+='<p class="muted">No source decisions recorded yet.</p>'
    for review in data["reviews"]:
        content+='<section class="panel"><strong>'+escape(review["actor"]+' · '+review["decision"].replace("_"," "))+'</strong><p>'+escape(review["notes"])+'</p></section>'
    return page("Review monthly source package",content)

def package_query(path):
    query=parse_qs(urlsplit(path).query,max_num_fields=2)
    if set(query)!={"id"} or len(query["id"])!=1:
        raise ValueError("One package ID required")
    package_id=query["id"][0]
    if len(package_id)!=64 or any(c not in "0123456789abcdef" for c in package_id):
        raise ValueError("Invalid package ID")
    return package_id

def handler_for(db_path):
    from complied.microsoft_identity import configured,settings as microsoft_settings
    public_origin=microsoft_settings()["COMPLIED_PUBLIC_ORIGIN"] if configured() else None
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,format,*args):
            # OAuth callbacks include short-lived codes in the URL; never log request paths.
            pass
        def origin(self):
            return public_origin or "http://127.0.0.1:"+str(self.server.server_port)
        def allowed_host(self):
            return self.headers.get("Host")==urlsplit(self.origin()).netloc
        def token(self):
            cookies=SimpleCookie()
            try:
                cookies.load(self.headers.get("Cookie",""))
                return cookies["complied_session"].value if "complied_session" in cookies else ""
            except Exception:
                return ""
        def flow_cookie(self):
            cookies=SimpleCookie()
            try:
                cookies.load(self.headers.get("Cookie",""))
                return cookies["complied_flow"].value if "complied_flow" in cookies else ""
            except Exception:
                return ""
        def respond(self,status,content,cookie=None,content_type="text/html; charset=utf-8",download=False):
            payload=content.encode()
            self.send_response(status)
            self.send_header("Content-Type",content_type)
            if download: self.send_header("Content-Disposition",'attachment; filename="complied-source-review.json"')
            self.send_header("Content-Length",str(len(payload)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            if cookie:
                for item in cookie if isinstance(cookie,(list,tuple)) else (cookie,):
                    self.send_header("Set-Cookie",item)
            self.end_headers()
            self.wfile.write(payload)
        def redirect(self,target,cookie=None):
            self.send_response(303)
            self.send_header("Location",target)
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length","0")
            if cookie:
                for item in cookie if isinstance(cookie,(list,tuple)) else (cookie,):
                    self.send_header("Set-Cookie",item)
            self.end_headers()
        def setup(self):
            super().setup()
            self.connection.settimeout(15)
        def do_GET(self):
            if not self.allowed_host():
                self.send_error(403)
                return
            path=urlsplit(self.path).path
            if path=="/auth/microsoft" and public_origin:
                from complied.microsoft_identity import begin
                db=connect(db_path)
                try:
                    url,browser=begin(db,"login")
                    self.redirect(url,"complied_flow="+browser+"; Secure; HttpOnly; SameSite=Lax; Path=/auth; Max-Age=600")
                except (ValueError,PermissionError):
                    self.send_error(403)
                finally:
                    db.close()
                return
            if path=="/auth/callback" and public_origin:
                from complied.microsoft_identity import finish
                db=connect(db_path)
                try:
                    if len(self.path)>8192:
                        raise ValueError("Callback too large")
                    query=parse_qs(urlsplit(self.path).query,keep_blank_values=True,max_num_fields=4)
                    if any(len(v)!=1 for v in query.values()) or not set(query)<=set(("code","state","session_state")):
                        raise ValueError("Invalid callback")
                    session,kind=finish(db,self.flow_cookie(),{k:v[0] for k,v in query.items()},self.token())
                    clear="complied_flow=; Secure; HttpOnly; SameSite=Lax; Path=/auth; Max-Age=0"
                    cookies=[clear]
                    if kind=="login":
                        cookies.append("complied_session="+session+"; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600")
                    self.redirect("/" if kind=="login" else "/reminders",cookies)
                except Exception:
                    # A provider failure must not log its callback parameters or token details.
                    self.send_error(403)
                finally:
                    db.close()
                return
            if path=="/login":
                if public_origin:
                    self.redirect("/auth/microsoft")
                    return
                form='<form method="post" action="/login">'+field("user","User")+field("password","Password",kind="password")+'<button>Sign in</button></form>'
                self.respond(200,page("Project Complied sign-in",form,public=True))
                return
            if path not in ("/","/register","/reminders","/microsoft-calendars","/schedules","/preparation","/package","/reconcile","/package-export"):
                self.send_error(404)
                return
            db=connect(db_path)
            try:
                user=authenticate(db,self.token())
                if path=="/package-export":
                    from complied.package_review import export_package
                    package_id=package_query(self.path)
                    self.respond(200,export_package(db,self.token(),package_id),content_type="application/json; charset=utf-8",
                                 download=True)
                    return
                elif path=="/reconcile":
                    content=reconcile_page(db,package_query(self.path))
                elif path=="/package":
                    content=package_page(db,user,package_query(self.path))
                elif path=="/microsoft-calendars" and public_origin:
                    content=calendars_page(db,user,self.token())
                elif path=="/preparation":
                    content=preparation_page(db,user)
                elif path=="/schedules":
                    content=schedules_page(db,user)
                elif path=="/reminders":
                    content=reminders_page(db,user)
                elif path=="/register":
                    content=register_page(db,user)
                elif path=="/microsoft-calendars":
                    raise ValueError("Microsoft not configured")
                else:
                    from complied.web import render
                    today=datetime.now(ZoneInfo("America/New_York")).date()
                    from complied.workflow import months
                    content=render(dashboard(db,today),today,months(db))
                self.respond(200,content)
            except PermissionError:
                self.redirect("/login")
            except (ValueError,KeyError):
                self.send_error(404)
            finally:
                db.close()
        def do_POST(self):
            if not self.allowed_host() or self.headers.get("Origin")!=self.origin():
                self.send_error(403)
                return
            path=urlsplit(self.path).path
            if path not in ("/login","/logout","/create","/edit","/review","/configure-reminders","/queue-reminder","/schedule-preview","/schedule-confirm","/package-review","/upload-sales","/connect-microsoft","/disconnect-microsoft"):
                self.send_error(404)
                return
            try:
                if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length",[]))!=1:
                    raise ValueError("Ambiguous body length")
                length=int(self.headers["Content-Length"])
                content_type=self.headers.get("Content-Type","")
                if path=="/upload-sales":
                    from complied.uploads import MAX_REQUEST,parse_upload
                    if not 0<length<=MAX_REQUEST:
                        raise ValueError("Upload exceeds the request limit")
                    fields=parse_upload(content_type,self.rfile.read(length))
                else:
                    if not 0<length<=16384 or content_type.split(";")[0]!="application/x-www-form-urlencoded":
                        raise ValueError("Expected a form")
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
                    if public_origin:
                        raise PermissionError("Use Microsoft sign-in")
                    token,_=login(db,fields["user"],fields["password"])
                    self.redirect("/",f"complied_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600")
                    return
                token=self.token()
                user=authenticate(db,token)
                if not hmac.compare_digest(user["csrf"],fields.get("csrf","")):
                    raise PermissionError("Invalid request token")
                if path=="/logout":
                    logout(db,token)
                    self.redirect("/login","complied_session=; "+("Secure; " if public_origin else "")+"HttpOnly; SameSite=Lax; Path=/; Max-Age=0")
                elif path=="/connect-microsoft":
                    if not public_origin:
                        raise PermissionError("Microsoft not configured")
                    from complied.microsoft_identity import begin
                    url,browser=begin(db,"connect",token)
                    self.redirect(url,"complied_flow="+browser+"; Secure; HttpOnly; SameSite=Lax; Path=/auth; Max-Age=600")
                elif path=="/disconnect-microsoft":
                    if not public_origin:
                        raise PermissionError("Microsoft not configured")
                    from complied.microsoft_identity import disconnect
                    disconnect(db,token)
                    self.redirect("/reminders")
                elif path=="/upload-sales":
                    from complied.imports import import_pair
                    import_pair(db,token,fields["ivy"],fields["pantops"])
                    self.redirect("/preparation")
                elif path=="/package-review":
                    from complied.package_review import record_review
                    record_review(db,token,fields["package_id"],int(fields["revision"]),fields["decision"],fields["notes"],fields["context"])
                    self.redirect("/preparation")
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
                    if public_origin:
                        from complied.microsoft_identity import graph_token
                        from complied.microsoft import GraphHTTPTransport
                        if user["role"]!="owner":
                            raise PermissionError("Owner required")
                        calendars=GraphHTTPTransport(graph_token(db,user["id"]),enabled=True).get_calendars()
                        if fields["calendar_id"] not in {item["id"] for item in calendars}:
                            raise ValueError("Select a Microsoft calendar")
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
