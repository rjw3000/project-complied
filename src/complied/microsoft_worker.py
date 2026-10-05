"""One-at-a-time scheduled Microsoft reminders; unknown outcomes need reconciliation."""
import argparse
import os
import time
from complied.deadlines import connect
from complied.microsoft import GraphHTTPTransport
from complied.microsoft_identity import configured,settings,graph_token
from complied.reminders import MicrosoftGraphAdapter,dispatch_one,recover_inflight

def run_once(db):
    if not configured() or os.environ.get("COMPLIED_LIVE_SEND")!="1":
        raise PermissionError("Live worker is disabled")
    config=settings()
    # Acquire a usable delegated token before claiming the next durable request.
    token=graph_token(db,"ms:"+config["COMPLIED_OWNER_OID"].lower())
    return dispatch_one(db,MicrosoftGraphAdapter(GraphHTTPTransport(token,enabled=True).post))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",default=os.environ.get("COMPLIED_DB","var/demo.sqlite3"))
    parser.add_argument("--interval",type=int,default=60)
    parser.add_argument("--once",action="store_true")
    args=parser.parse_args()
    if not 30<=args.interval<=3600:
        raise ValueError("Worker interval must be 30..3600 seconds")
    if not configured() or os.environ.get("COMPLIED_LIVE_SEND")!="1":
        raise PermissionError("Live worker needs explicit enablement")
    db=connect(args.db)
    try:
        recover_inflight(db)
        while True:
            try:
                status=run_once(db)
            except Exception:
                # Graph/identity errors must not put credentials in logs or claim queued sends.
                status="connection_unavailable"
            print("Reminder worker: "+(status or "no_due_request"),flush=True)
            if args.once:
                return
            time.sleep(args.interval)
    finally:
        db.close()

if __name__=="__main__":
    main()
