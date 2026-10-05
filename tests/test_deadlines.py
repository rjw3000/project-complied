import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect,add_obligation,add_task,complete_task,dashboard,seed
from complied.web import render

class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
    def tearDown(self):
        self.db.close()
    def obligation(self,oid="d",**kwargs):
        args=dict(id=oid,title="Test",jurisdiction="Demo",owner="Owner",
                  status="applicable",source="urn:demo",reviewed=True)
        args.update(kwargs)
        add_obligation(self.db,**args)
    def test_unknown_does_not_get_deadline_or_completion(self):
        self.obligation(status="unresolved",reviewed=False,source="")
        with self.assertRaises(ValueError): add_task(self.db,"d","period","2026-10-20")
        add_task(self.db,"d","period")
        row=dashboard(self.db,date(2026,10,5))[0]
        self.assertEqual(row["state"],"unresolved")
        with self.assertRaises(ValueError): complete_task(self.db,row["id"],"2026-10-05")
    def test_review_evidence_required(self):
        for kwargs in [dict(reviewed=False),dict(source="")]:
            with self.assertRaises(ValueError): self.obligation(**kwargs)
    def test_duplicate_task_and_foreign_scope(self):
        self.obligation()
        add_task(self.db,"d","period","2026-10-20")
        add_task(self.db,"d","period","2026-10-20")
        self.assertEqual(len(dashboard(self.db,date(2026,10,5))),1)
        with self.assertRaises(ValueError): add_task(self.db,"missing","period")
    def test_due_boundary_and_completion(self):
        self.obligation()
        for period,due in [("before","2026-10-04"),("today","2026-10-05"),("after","2026-10-06")]:
            add_task(self.db,"d",period,due)
        rows=dashboard(self.db,date(2026,10,5))
        self.assertEqual([r["state"] for r in rows],["overdue","due_today","upcoming"])
        complete_task(self.db,rows[0]["id"],"2026-10-05")
        self.assertEqual(dashboard(self.db,date(2026,10,5))[0]["state"],"completed")
    def test_invalid_date_and_inapplicable(self):
        self.obligation(status="not_applicable")
        with self.assertRaises(ValueError): add_task(self.db,"d","period")
        self.obligation("other")
        with self.assertRaises(ValueError): add_task(self.db,"other","period","2026-02-30")
    def test_seed_repeat_and_html_escape(self):
        seed(self.db)
        seed(self.db)
        rows=dashboard(self.db,date(2026,10,5))
        self.assertEqual(len(rows),8)
        self.assertEqual(sum(r["state"]=="unresolved" for r in rows),5)
        rows[0]["title"]="<script>alert(1)</script>"
        page=render(rows,date(2026,10,5))
        self.assertNotIn("<script>",page)
        self.assertIn("&lt;script&gt;",page)
