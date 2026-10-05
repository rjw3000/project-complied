import json
import secrets
import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.access import create_user,login,disable_user
from complied.deadlines import connect
from complied.imports import import_snapshot,prepare
from complied.package_review import summary,context,record_review,export_package
from test_imports import raw

class PackageReviewTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        password=secrets.token_urlsafe(24)
        create_user(self.db,"owner","owner",password)
        self.token,_=login(self.db,"owner",password)
        self.ids=[import_snapshot(self.db,self.token,raw()),import_snapshot(self.db,self.token,raw("pantops"))]
        self.package_id,_=prepare(self.db,self.token,self.ids)
    def tearDown(self): self.db.close()
    def review(self,decision="sources_reviewed",notes="Synthetic source review"):
        data=summary(self.db,self.package_id)
        fingerprint,_=context(self.db,data["manifest"])
        return record_review(self.db,self.token,self.package_id,data["review_revision"],decision,notes,fingerprint)
    def test_review_cannot_make_return_ready(self):
        self.assertEqual(summary(self.db,self.package_id)["review_state"],"needs_review")
        self.review()
        data=summary(self.db,self.package_id)
        self.assertEqual(data["review_state"],"sources_reviewed")
        self.assertFalse(data["return_ready"])
        self.assertGreater(len(data["blockers"]),0)
        export=json.loads(export_package(self.db,self.token,self.package_id))
        self.assertEqual(export["export_type"],"source_review_packet_not_a_tax_return")
    def test_new_source_stales_review_not_other_period(self):
        self.review()
        import_snapshot(self.db,self.token,raw(period="2026-11"))
        self.assertFalse(summary(self.db,self.package_id)["review_stale"])
        import_snapshot(self.db,self.token,raw(taxable="900.00",control="4900.00"))
        data=summary(self.db,self.package_id)
        self.assertTrue(data["review_stale"])
        self.assertEqual(data["review_state"],"needs_review")
        self.review(notes="Reviewed alternate source version and retained original")
        self.assertFalse(summary(self.db,self.package_id)["review_stale"])
    def test_stale_revision_or_context_denied(self):
        data=summary(self.db,self.package_id)
        fingerprint,_=context(self.db,data["manifest"])
        self.review()
        with self.assertRaises(ValueError):
            record_review(self.db,self.token,self.package_id,0,"rejected","Older form",fingerprint)
        import_snapshot(self.db,self.token,raw(taxable="900.00",control="4900.00"))
        with self.assertRaises(ValueError):
            record_review(self.db,self.token,self.package_id,1,"sources_reviewed","Older evidence set",fingerprint)
        self.assertEqual(len(summary(self.db,self.package_id)["reviews"]),1)
    def test_review_history_immutable(self):
        self.review("needs_information")
        self.review("rejected")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db: self.db.execute("DELETE FROM package_reviews")
        self.assertEqual([r["decision"] for r in summary(self.db,self.package_id)["reviews"]],["needs_information","rejected"])
    def test_anonymous_revoked_and_invalid_decision(self):
        with self.assertRaises(PermissionError): export_package(self.db,"",self.package_id)
        for decision,notes in [("approve_filing","No"),("sources_reviewed","")]:
            with self.assertRaises(ValueError): self.review(decision,notes)
        disable_user(self.db,"owner")
        with self.assertRaises(PermissionError): self.review()
    def test_missing_package_rejected(self):
        with self.assertRaises(ValueError): summary(self.db,"missing")
