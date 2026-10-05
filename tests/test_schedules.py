import secrets
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.access import create_user,login,mutate,disable_user
from complied.deadlines import connect,add_obligation,add_task,complete_task
from complied.schedules import propose,confirm
from complied.reminders import configure,enqueue,list_outbox

class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        password=secrets.token_urlsafe(24)
        create_user(self.db,"owner","owner",password)
        create_user(self.db,"delegate","delegate",password)
        self.token,_=login(self.db,"owner",password)
        self.delegate,_=login(self.db,"delegate",password)
        add_obligation(self.db,id="d",title="Demo",jurisdiction="Demo",owner="Owner",status="applicable",source="urn:demo",reviewed=True)
        self.definition=dict(anchor="2026-01-01",period_months=1,due_month_offset=0,due_day=15,short_month="reject",
                             roll="none",holidays=[],calendar_start=None,calendar_end=None,effective_start="2026-01-01",effective_end="2027-01-01")
    def tearDown(self): self.db.close()
    def proposal(self,day=15,count=1):
        return propose(self.db,self.token,"d",dict(self.definition,due_day=day),"urn:demo","2026-10",count,"Synthetic review")
    def task(self):
        return self.db.execute("SELECT * FROM tasks WHERE obligation_id='d' AND period='2026-10'").fetchone()
    def test_preview_then_confirm_once(self):
        proposal,preview=self.proposal()
        self.assertIsNone(self.task())
        self.assertEqual(preview["rows"][0]["action"],"create")
        confirm(self.db,self.token,proposal)
        self.assertEqual(self.task()["due_date"],"2026-11-15")
        with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
    def test_manual_date_replacement_history_and_reminder_identity(self):
        add_task(self.db,"d","2026-10","2026-11-10")
        configure(self.db,self.token,"demo@example.invalid","calendar")
        old=enqueue(self.db,self.token,self.task()["id"],"email",7)
        proposal,preview=self.proposal()
        self.assertEqual(preview["rows"][0]["action"],"replace")
        confirm(self.db,self.token,proposal)
        self.assertEqual(self.task()["schedule_revision"],1)
        new=enqueue(self.db,self.token,self.task()["id"],"email",7)
        self.assertNotEqual(old,new)
        self.assertEqual(self.db.execute("SELECT status FROM reminder_outbox WHERE id=?",(old,)).fetchone()[0],"cancelled")
        self.assertGreater(self.db.execute("SELECT COUNT(*) FROM audit_events WHERE action='apply-schedule'").fetchone()[0],0)
    def test_completed_change_blocks_entire_batch(self):
        add_task(self.db,"d","2026-10","2026-11-10")
        complete_task(self.db,self.task()["id"],"2026-11-10")
        proposal,preview=self.proposal(count=2)
        self.assertEqual(preview["rows"][0]["action"],"blocked_completed")
        with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],1)
    def test_stale_preview_rejected(self):
        proposal,_=self.proposal()
        add_task(self.db,"d","2026-10","2026-11-12")
        with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
        self.assertEqual(self.task()["due_date"],"2026-11-12")
    def test_wrong_actor_expiry_revocation(self):
        proposal,_=self.proposal()
        with self.assertRaises(ValueError): confirm(self.db,self.delegate,proposal)
        with self.db: self.db.execute("UPDATE schedule_proposals SET expires=0 WHERE id=?",(proposal,))
        with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
        proposal,_=self.proposal()
        disable_user(self.db,"owner")
        with self.assertRaises(PermissionError): confirm(self.db,self.token,proposal)
    def test_external_unknown_or_created_blocks_replacement(self):
        add_task(self.db,"d","2026-10","2026-11-10")
        configure(self.db,self.token,"demo@example.invalid","calendar")
        key=enqueue(self.db,self.token,self.task()["id"],"calendar")
        for status in ["unknown","inflight","created"]:
            with self.db: self.db.execute("UPDATE reminder_outbox SET status=? WHERE id=?",(status,key))
            proposal,preview=self.proposal()
            self.assertEqual(preview["rows"][0]["action"],"blocked_external")
            with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
    def test_reminder_race_invalidates_preview(self):
        add_task(self.db,"d","2026-10","2026-11-10")
        configure(self.db,self.token,"demo@example.invalid","calendar")
        key=enqueue(self.db,self.token,self.task()["id"],"email")
        proposal,_=self.proposal()
        with self.db: self.db.execute("UPDATE reminder_outbox SET status='inflight' WHERE id=?",(key,))
        with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
    def test_new_review_rejects_preview(self):
        proposal,_=self.proposal()
        mutate(self.db,self.token,"review",dict(id="d",revision="0",status="applicable",source="urn:changed",rationale="Change"))
        with self.assertRaises(ValueError): confirm(self.db,self.token,proposal)
    def test_identical_confirm_preserves_completed_task(self):
        proposal,_=self.proposal()
        confirm(self.db,self.token,proposal)
        complete_task(self.db,self.task()["id"],"2026-11-15")
        proposal,preview=self.proposal()
        self.assertEqual(preview["rows"][0]["action"],"keep")
        confirm(self.db,self.token,proposal)
        self.assertEqual(self.task()["completed_on"],"2026-11-15")
