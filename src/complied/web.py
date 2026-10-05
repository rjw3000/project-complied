"""Read-only loopback dashboard for synthetic development data."""
import argparse
from collections import Counter
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from complied.deadlines import connect, dashboard

def render(rows, today, monthly=None):
    from complied.editor import page
    counts=Counter(row["state"] for row in rows)
    cards="".join('<div class="card"><strong>'+str(counts[state])+'</strong><span>'+label+'</span></div>'
        for state,label in [("overdue","Overdue"),("due_today","Due today"),
                            ("upcoming","Upcoming"),("unresolved","Needs verification"),
                            ("completed","Completed"),("not_applicable","Not applicable")])
    body=""
    for row in rows:
        values=[row["title"],row["jurisdiction"],row["period"],row["due_date"] or "Not verified",
                row["state"].replace("_"," "),row["owner"],row["source"] or "Source needed",row["rationale"]]
        body+="<tr>"+"".join("<td>"+escape(str(value))+"</td>" for value in values)+"</tr>"
    if not body:
        body='<tr><td colspan="8">No requirements recorded. Add one to begin review.</td></tr>'
    monthly=monthly or []
    if monthly:
        item=monthly[0]
        summary=('<section class="action-card"><h2>Monthly sales · '+escape(item["manifest"]["period"])+'</h2>'
                 '<p>'+escape(item["next_action"])+'</p>'
                 '<a class="button-link" href="'+escape(item["next_href"],quote=True)+'">Continue monthly workflow</a></section>')
        summary+='<div class="panel"><h2>Months in progress</h2><ul>'
        for item in monthly[:6]:
            summary+='<li><a href="/reconcile?id='+escape(item["package_id"],quote=True)+'">'+escape(item["manifest"]["period"])+'</a> · '+escape(item["review_state"].replace("_"," "))+'</li>'
        summary+='</ul></div>'
    else:
        summary=('<section class="action-card"><h2>Start monthly sales</h2>'
                 '<p>Upload the two store reports, reconcile totals, then record source review.</p>'
                 '<a class="button-link" href="/preparation">Start monthly workflow</a></section>')
    priority=''
    if counts["overdue"]:
        priority+='<li><a href="#obligations">Review '+str(counts["overdue"])+' overdue deadline(s)</a></li>'
    if counts["unresolved"]:
        priority+='<li><a href="/register">Verify '+str(counts["unresolved"])+' unresolved requirement(s)</a></li>'
    if priority:
        summary+='<section class="panel"><h2>Other actions</h2><ul>'+priority+'</ul></section>'
    content=('<p class="muted">See what is due and which requirements need review. Business date: '
             +escape(str(today))+' · America/New_York</p>'
             '<div class="notice">Synthetic demo only. Dates are illustrative. Verify each statutory rule before relying on it.</div>'
             '<section class="cards" aria-label="Task counts">'+cards+'</section>'
             +summary+
             '<div class="table" id="obligations"><table><caption>Obligation register and period tasks</caption>'
             '<thead><tr><th>Requirement</th><th>Jurisdiction</th><th>Period</th><th>Deadline</th>'
             '<th>Status</th><th>Owner</th><th>Source</th><th>Review context</th></tr></thead><tbody>'
             +body+'</tbody></table></div>'
             '<p class="muted">Unverified requirements stay visible until reviewed.</p>')
    return page("Compliance calendar",content)


def handler_for(db_path):
    from complied.editor import handler_for as authenticated_handler
    return authenticated_handler(db_path)

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
