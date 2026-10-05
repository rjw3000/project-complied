import json
import secrets
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect,add_obligation,add_task,complete_task
from complied.access import create_user,login,mutate
from complied.reminders import configure,enqueue,dispatch_one,list_outbox,recover_inflight,MicrosoftGraphAdapter

class Transport:
    def __init__(self,result):
        self.result=result
        self.calls=0
    def send(self,channel,payload):
        self.calls+=1
        if isinstance(self.result,Exception): raise self.result
        return self.result

class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        password=secrets.token_urlsafe(24)
        create_user(self.db,"owner","owner",password)
        create_user(self.db,"delegate","delegate",password)
        self.token,_=login(self.db,"owner",password)
        self.delegate,_=login(self.db,"delegate",password)
        add_obligation(self.db,id="d",title="Demo",jurisdiction="Demo",owner="Demo",
                       status="applicable",source="urn:demo",reviewed=True)
        add_task(self.db,"d","2026-10","2026-11-15")
        self.task_id=self.db.execute("SELECT id FROM tasks").fetchone()[0]
        configure(self.db,self.token,"demo@example.invalid","calendar-demo")
        self.now=2000000000
    def tearDown(self):
        self.db.close()
    def test_destination_owner_only(self):
        with self.assertRaises(PermissionError): configure(self.db,self.delegate,"other@example.invalid","calendar")
    def test_dedup_and_calendar_single_event(self):
        first=enqueue(self.db,self.token,self.task_id,"email",7)
        self.assertEqual(first,enqueue(self.db,self.token,self.task_id,"email",7))
        self.assertNotEqual(first,enqueue(self.db,self.token,self.task_id,"email",3))
        event=enqueue(self.db,self.delegate,self.task_id,"calendar",7)
        self.assertEqual(event,enqueue(self.db,self.delegate,self.task_id,"calendar",1))
        self.assertEqual(len(list_outbox(self.db)),3)
    def test_unknown_and_completed_tasks_rejected(self):
        complete_task(self.db,self.task_id,"2026-11-15")
        with self.assertRaises(ValueError): enqueue(self.db,self.token,self.task_id,"email",7)
        with self.assertRaises(ValueError): enqueue(self.db,self.token,999,"email",7)
    def test_due_time_business_timezone(self):
        key=enqueue(self.db,self.token,self.task_id,"email",7)
        row=self.db.execute("SELECT * FROM reminder_outbox WHERE id=?",(key,)).fetchone()
        when=datetime.fromtimestamp(row["scheduled_at"],ZoneInfo("America/New_York"))
        self.assertEqual(when.strftime("%Y-%m-%d %H:%M"),"2026-11-08 09:00")
        transport=Transport(("accepted",None))
        self.assertIsNone(dispatch_one(self.db,transport,now=row["scheduled_at"]-1))
        self.assertEqual(transport.calls,0)
    def test_acceptance_does_not_resend(self):
        enqueue(self.db,self.token,self.task_id,"email",7)
        transport=Transport(("accepted",None))
        self.assertEqual(dispatch_one(self.db,transport,now=self.now),"accepted")
        self.assertIsNone(dispatch_one(self.db,transport,now=self.now))
        self.assertEqual(transport.calls,1)
        self.assertEqual(list_outbox(self.db)[0]["status"],"accepted")
    def test_timeout_unknown_no_retry(self):
        enqueue(self.db,self.token,self.task_id,"email",7)
        transport=Transport(TimeoutError("sensitive details"))
        self.assertEqual(dispatch_one(self.db,transport,now=self.now),"unknown")
        self.assertIsNone(dispatch_one(self.db,transport,now=self.now))
        self.assertNotIn("sensitive",list_outbox(self.db)[0]["error"])
    def test_changed_task_or_destination_cancels(self):
        enqueue(self.db,self.token,self.task_id,"email",7)
        mutate(self.db,self.token,"edit",dict(id="d",revision="0",title="Changed",jurisdiction="Demo",owner="Demo"))
        transport=Transport(("accepted",None))
        self.assertEqual(dispatch_one(self.db,transport,now=self.now),"cancelled")
        self.assertEqual(transport.calls,0)
        self.assertTrue(list_outbox(self.db)[0]["needs_reconciliation"])
    def test_destination_change_cancels(self):
        enqueue(self.db,self.token,self.task_id,"calendar")
        configure(self.db,self.token,"changed@example.invalid","new-calendar")
        transport=Transport(("created","event"))
        self.assertEqual(dispatch_one(self.db,transport,now=self.now),"cancelled")
        self.assertEqual(transport.calls,0)
    def test_crash_recovery_unknown(self):
        key=enqueue(self.db,self.token,self.task_id,"email",7)
        with self.db: self.db.execute("UPDATE reminder_outbox SET status='inflight' WHERE id=?",(key,))
        recover_inflight(self.db)
        self.assertEqual(list_outbox(self.db)[0]["status"],"unknown")
    def test_graph_payload_and_response(self):
        key=enqueue(self.db,self.token,self.task_id,"calendar")
        row=self.db.execute("SELECT payload FROM reminder_outbox WHERE id=?",(key,)).fetchone()
        payload=json.loads(row["payload"])
        self.assertEqual(payload["body"]["transactionId"],key)
        self.assertEqual(payload["body"]["end"]["dateTime"],"2026-11-16T00:00:00")
        self.assertEqual(payload["body"]["start"]["timeZone"],"Eastern Standard Time")
        adapter=MicrosoftGraphAdapter(lambda path,body:(201,{"id":"synthetic-event"}))
        self.assertEqual(dispatch_one(self.db,adapter,now=self.now),"created")
        self.assertEqual(list_outbox(self.db)[0]["provider_id"],"synthetic-event")
    def test_mail_accepted_and_http_failure(self):
        adapter=MicrosoftGraphAdapter(lambda path,body:(202,{}))
        self.assertEqual(adapter.send("email",{"path":"/me/sendMail","body":{}}),("accepted",None))
        adapter=MicrosoftGraphAdapter(lambda path,body:(401,{}))
        self.assertEqual(adapter.send("email",{"path":"/me/sendMail","body":{}}),("failed",None))
        adapter=MicrosoftGraphAdapter(lambda path,body:(503,{}))
        self.assertEqual(adapter.send("email",{"path":"/me/sendMail","body":{}}),("unknown",None))
