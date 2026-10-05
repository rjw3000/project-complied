import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect,add_obligation,add_task,complete_task,dashboard,SCHEMA
from complied.recurrence import register_rule,generate,due_date

class RecurrenceTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        add_obligation(self.db,id="d",title="Demo",jurisdiction="Demo",owner="Demo",
                       status="applicable",source="urn:demo",reviewed=True)
        self.definition=dict(anchor="2024-01-01",period_months=1,due_month_offset=0,
            due_day=15,short_month="reject",roll="none",holidays=[],
            calendar_start=None,calendar_end=None,
            effective_start="2024-01-01",effective_end="2027-12-01")
    def tearDown(self):
        self.db.close()
    def rule(self,**changes):
        definition=dict(self.definition,**changes)
        return register_rule(self.db,"d",definition,source="urn:demo",
                             reviewer="Demo",reviewed_on="2026-10-05")
    def test_monthly_year_rollover_and_idempotency(self):
        rule=self.rule()
        ids=generate(self.db,rule,"2026-11",3)
        self.assertEqual(ids,generate(self.db,rule,"2026-11",3))
        rows=dashboard(self.db,date(2026,10,5))
        self.assertEqual([r["due_date"] for r in rows],["2026-12-15","2027-01-15","2027-02-15"])
        self.assertTrue(all(r["rule_id"]==rule for r in rows))
    def test_quarter_and_year_alignment(self):
        definition=dict(self.definition,period_months=3)
        self.assertEqual(due_date(definition,"2026-10"),"2027-01-15")
        with self.assertRaises(ValueError): due_date(definition,"2026-11")
        self.assertEqual(due_date(dict(definition,period_months=12),"2026-01"),"2027-01-15")
    def test_leap_year_and_explicit_short_month_policy(self):
        definition=dict(self.definition,due_day=31)
        with self.assertRaises(ValueError): due_date(definition,"2024-01")
        definition["short_month"]="last_day"
        self.assertEqual(due_date(definition,"2024-01"),"2024-02-29")
        self.assertEqual(due_date(definition,"2025-01"),"2025-02-28")
    def test_weekend_holiday_and_coverage(self):
        definition=dict(self.definition,due_day=31,roll="next_business_day",
                        holidays=["2026-11-02"],calendar_start="2026-10-01",calendar_end="2026-11-03")
        self.assertEqual(due_date(definition,"2026-09"),"2026-11-03")
        definition["calendar_end"]="2026-11-02"
        with self.assertRaises(ValueError): due_date(definition,"2026-09")
    def test_changed_rule_conflicts_preserve_completion(self):
        old=self.rule()
        ids=generate(self.db,old,"2026-10",1)
        complete_task(self.db,ids[0],"2026-11-15")
        changed=self.rule(due_day=16)
        with self.assertRaises(ValueError): generate(self.db,changed,"2026-10",1)
        row=dashboard(self.db,date(2026,12,1))[0]
        self.assertEqual((row["due_date"],row["completed_on"],row["rule_id"]),
                         ("2026-11-15","2026-11-15",old))
    def test_batch_rolls_back_on_later_conflict(self):
        rule=self.rule()
        add_task(self.db,"d","2026-11","2026-12-15")
        with self.assertRaises(ValueError): generate(self.db,rule,"2026-10",2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],1)
    def test_review_gates_and_revocation(self):
        with self.assertRaises(ValueError):
            register_rule(self.db,"d",self.definition,source="",reviewer="Demo",reviewed_on="2026-10-05")
        rule=self.rule()
        with self.db: self.db.execute("UPDATE obligations SET status='unresolved',reviewed=0 WHERE id='d'")
        with self.assertRaises(ValueError): generate(self.db,rule,"2026-10",1)
    def test_effective_range_and_validation(self):
        for changes in [dict(period_months=True),dict(due_day=0),dict(roll="guess"),
                        dict(anchor="2026-01-02"),dict(holidays=["bad"]),
                        dict(calendar_start="2026-01-01")]:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError): self.rule(**changes)
        rule=self.rule(effective_end="2026-10-01")
        with self.assertRaises(ValueError): generate(self.db,rule,"2026-10",2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],0)
    def test_rule_storage_is_immutable(self):
        rule=self.rule()
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db: self.db.execute("UPDATE deadline_rules SET source='changed' WHERE id=?",(rule,))
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db: self.db.execute("DELETE FROM deadline_rules WHERE id=?",(rule,))
    def test_add_task_conflict_is_not_silently_ignored(self):
        add_task(self.db,"d","2026-10","2026-11-15")
        with self.assertRaises(ValueError): add_task(self.db,"d","2026-10","2026-11-16")
    def test_v1_migration_preserves_rows_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            old=sqlite3.connect(path)
            old.executescript(SCHEMA)
            old.execute("INSERT INTO schema_versions VALUES(1)")
            old.execute("INSERT INTO obligations VALUES('old','Old','Demo','unresolved','','','Owner',NULL,0)")
            old.execute("INSERT INTO tasks(obligation_id,period) VALUES('old','2026-10')")
            old.commit()
            old.close()
            for _ in range(2):
                new=connect(path)
                self.assertEqual(new.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],1)
                self.assertEqual(new.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0],5)
                new.close()

    def test_register_includes_obligations_without_tasks(self):
        add_obligation(self.db,id="unresolved",title="Discovery",jurisdiction="Demo",owner="Demo")
        add_obligation(self.db,id="excluded",title="Excluded",jurisdiction="Demo",owner="Demo",
                       status="not_applicable",rationale="Owner review")
        rows=dashboard(self.db,date(2026,10,5))
        states={r["obligation_id"]:r["state"] for r in rows}
        self.assertEqual(states,{"d":"unresolved","unresolved":"unresolved","excluded":"not_applicable"})
        self.assertTrue(all(r["id"] is None for r in rows))
        self.assertTrue(all(r["period"]=="No period" for r in rows))
