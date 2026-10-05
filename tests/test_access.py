import secrets
import sys
import unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect,add_obligation,add_task,dashboard
from complied.access import create_user,login,authenticate,logout,disable_user,authorize,mutate
from complied.recurrence import register_rule,generate

class AccessTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        self.password=secrets.token_urlsafe(24)
        create_user(self.db,"owner","owner",self.password)
        create_user(self.db,"delegate","delegate",self.password)
        self.token,_=login(self.db,"owner",self.password)
    def tearDown(self):
        self.db.close()
    def fields(self):
        return dict(id="test",title="Demo requirement",jurisdiction="Demo",owner="Demo")
    def test_password_and_expiry(self):
        with self.assertRaises(PermissionError): login(self.db,"owner","incorrect")
        token,_=login(self.db,"owner",self.password,now=100)
        self.assertEqual(authenticate(self.db,token,now=101)["id"],"owner")
        with self.assertRaises(PermissionError): authenticate(self.db,token,now=3700)
    def test_logout_and_revocation(self):
        logout(self.db,self.token)
        with self.assertRaises(PermissionError): authenticate(self.db,self.token)
        token,_=login(self.db,"delegate",self.password)
        disable_user(self.db,"delegate")
        with self.assertRaises(PermissionError): authenticate(self.db,token)
    def test_delegate_payment_denied(self):
        token,_=login(self.db,"delegate",self.password)
        self.assertEqual(authorize(self.db,token,"edit")["role"],"delegate")
        with self.assertRaises(PermissionError): authorize(self.db,token,"initiate_payment")
        self.assertEqual(authorize(self.db,self.token,"initiate_payment")["role"],"owner")
        with self.assertRaises(PermissionError): authorize(self.db,self.token,"unknown")
    def test_create_review_edit_and_audit(self):
        fields=self.fields()
        self.assertEqual(mutate(self.db,self.token,"create",fields),0)
        review=dict(id="test",revision="0",status="applicable",source="urn:demo",rationale="Synthetic reviewed facts")
        self.assertEqual(mutate(self.db,self.token,"review",review),1)
        add_task(self.db,"test","2026-10","2026-11-15")
        self.assertEqual(dashboard(self.db,date(2026,10,5))[0]["state"],"upcoming")
        mutate(self.db,self.token,"edit",dict(fields,revision="1",jurisdiction="Changed"))
        self.assertEqual(dashboard(self.db,date(2026,10,5))[0]["state"],"unresolved")
        mutate(self.db,self.token,"review",dict(review,revision="2"))
        self.assertEqual(dashboard(self.db,date(2026,10,5))[0]["state"],"unresolved")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0],4)
    def test_stale_edit_and_invalid_review_rollback(self):
        fields=self.fields()
        mutate(self.db,self.token,"create",fields)
        mutate(self.db,self.token,"edit",dict(fields,revision="0"))
        with self.assertRaises(ValueError): mutate(self.db,self.token,"edit",dict(fields,revision="0"))
        with self.assertRaises(ValueError): mutate(self.db,self.token,"review",dict(id="test",revision="1",status="applicable",source="",rationale=""))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0],2)
    def test_lockout(self):
        for _ in range(5):
            with self.assertRaises(PermissionError): login(self.db,"delegate","bad",now=100)
        with self.assertRaises(PermissionError): login(self.db,"delegate",self.password,now=101)
        self.assertTrue(login(self.db,"delegate",self.password,now=401))
    def test_old_rule_cannot_generate_after_new_review(self):
        add_obligation(self.db,id="d",title="Demo",jurisdiction="Demo",owner="Demo",
                       status="applicable",source="urn:demo",reviewed=True)
        definition=dict(anchor="2026-01-01",period_months=1,due_month_offset=0,due_day=15,
                        short_month="reject",roll="none",holidays=[],calendar_start=None,calendar_end=None,
                        effective_start="2026-01-01",effective_end="2027-01-01")
        rule=register_rule(self.db,"d",definition,source="urn:demo",reviewer="Demo",reviewed_on="2026-10-05")
        mutate(self.db,self.token,"review",dict(id="d",revision="0",status="applicable",source="urn:new",rationale="Changed"))
        with self.assertRaises(ValueError): generate(self.db,rule,"2026-10",1)
