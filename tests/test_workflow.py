import secrets
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.access import create_user,login
from complied.deadlines import connect
from complied.imports import import_pair,import_snapshot
from complied.package_review import context,record_review
from complied.workflow import assess,months
from test_imports import raw

class GuidedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        password=secrets.token_urlsafe(24)
        create_user(self.db,"owner","owner",password)
        self.token,_=login(self.db,"owner",password)
    def tearDown(self):
        self.db.close()
    def test_upload_reconcile_review_and_corrected_source(self):
        self.assertEqual(months(self.db),[])
        original,_=import_pair(self.db,self.token,raw(),raw("pantops"))
        first=assess(self.db,original)
        self.assertEqual(first["review_state"],"needs_review")
        self.assertEqual([item["state"] for item in first["checks"]],
                         ["passed","passed","passed","passed","passed","pending"])
        self.assertEqual(first["next_href"],"/reconcile?id="+original)
        fingerprint,_=context(self.db,first["manifest"])
        record_review(self.db,self.token,original,0,"sources_reviewed","Selected both original reports",fingerprint)
        self.assertEqual(months(self.db)[0]["review_state"],"sources_reviewed")
        self.assertFalse(months(self.db)[0]["return_ready"])
        revised=raw(taxable="900.00",control="4900.00")
        import_snapshot(self.db,self.token,revised)
        self.assertTrue(assess(self.db,original)["review_stale"])
        replacement,_=import_pair(self.db,self.token,revised,raw("pantops"))
        self.assertNotEqual(original,replacement)
        self.assertEqual(months(self.db)[0]["package_id"],replacement)
        self.assertEqual(months(self.db)[0]["review_state"],"needs_review")
        self.assertEqual(assess(self.db,replacement)["checks"][4]["state"],"attention")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM preparation_packages").fetchone()[0],2)
    def test_needs_information_guides_correction(self):
        key,_=import_pair(self.db,self.token,raw(),raw("pantops"))
        current=assess(self.db,key)
        fingerprint,_=context(self.db,current["manifest"])
        record_review(self.db,self.token,key,0,"needs_information","Check store report export",fingerprint)
        self.assertIn("Resolve missing information",months(self.db)[0]["next_action"])
        self.assertFalse(months(self.db)[0]["return_ready"])
