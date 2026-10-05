"""Read-only loopback dashboard for synthetic development data."""
import argparse
from collections import Counter
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from complied.deadlines import connect, dashboard

def render(rows, today):
    counts = Counter(row["state"] for row in rows)
    cards = "".join(f'<div class="card"><strong>{counts[state]}</strong><span>{label}</span></div>'
                    for state,label in [("overdue","Overdue"),("due_today","Due today"),
                                        ("upcoming","Upcoming"),("unresolved","Needs verification"),
                                        ("completed","Completed"),("not_applicable","Not applicable")])
    body = ""
    for row in rows:
        values = [row["title"], row["jurisdiction"], row["period"],
                  row["due_date"] or "Not verified",row["state"].replace("_"," "),
                  row["owner"],row["source"] or "Source needed",row["rationale"]]
        body += "<tr>" + "".join("<td>"+escape(str(value))+"</td>" for value in values) + "</tr>"
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Complied · Deadline prototype</title>
<style>
body{{margin:0;background:#f3f6fa;color:#192b40;font:16px system-ui,sans-serif}}
main{{max-width:1200px;margin:auto;padding:32px}}header{{margin-bottom:24px}}
h1{{margin:8px 0}}p{{line-height:1.6}}.notice{{padding:14px;background:#fff1c9;border-radius:8px}}
.cards{{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}}
.card{{background:white;padding:20px;min-width:120px;border-radius:12px;box-shadow:0 2px 6px #dbe2eb}}
strong{{display:block;font-size:30px}}span{{display:block;margin-top:8px}}
.table{{overflow:auto;background:white;border-radius:12px}}
table{{border-collapse:collapse;width:100%;text-align:left}}th,td{{padding:14px;border-bottom:1px solid #e3e9f0}}
th{{background:#e9eff7}}td{{vertical-align:top}}footer{{margin-top:24px;color:#526277}}
</style><main><header><small>PROJECT COMPLIED · INTERNAL PROTOTYPE</small>
<h1>Compliance calendar</h1><p>See what needs attention and which requirements still need verification.</p>
<div class="notice">Synthetic demo only. Dates are illustrative. No accounts, filings, payments or reminders are connected.</div>
</header><section class="cards" aria-label="Task counts">{cards}</section>
<p>Business date: {escape(str(today))} · America/New_York</p>
<div class="table"><table><caption>Obligation register and period tasks</caption>
<thead><tr><th>Requirement</th><th>Jurisdiction</th><th>Period</th><th>Deadline</th><th>Status</th>
<th>Owner</th><th>Source</th><th>Review context</th></tr></thead><tbody>{body}</tbody></table></div>
<footer>Missing facts stay visible. PostalMate preparation and authenticated review are next milestones.</footer></main></html>"""

def handler_for(db_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Host") not in {f"127.0.0.1:{self.server.server_port}",
                                                f"localhost:{self.server.server_port}"}:
                self.send_error(403)
                return
            if urlsplit(self.path).path != "/":
                self.send_error(404)
                return
            today = datetime.now(ZoneInfo("America/New_York")).date()
            db = connect(db_path)
            try:
                content = render(dashboard(db,today),today).encode()
            finally:
                db.close()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(content)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)
    return Handler

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",default="var/demo.sqlite3")
    parser.add_argument("--port",type=int,default=8080)
    args = parser.parse_args()
    with HTTPServer(("127.0.0.1",args.port),handler_for(args.db)) as server:
        print(f"Synthetic dashboard: http://127.0.0.1:{args.port}")
        server.serve_forever()

if __name__ == "__main__":
    main()
