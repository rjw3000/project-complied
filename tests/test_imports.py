import json
import secrets
import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.access import create_user,login
from complied.deadlines import connect
from complied.imports import import_snapshot,prepare,parse,HEADERS

def raw(store="ivy",period="2026-10",taxable="1000.00",nontaxable="4000.00",control="5000.00",tax="53.00"):
    return (",".join(HEADERS)+"\n"+",".join([store,period,taxable,nontaxable,control,tax])+"\n").encode()

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        password=secrets.token_urlsafe(24)
        create_user(self.db,"owner","owner",password)
        self.token,_=login(self.db,"owner",password)
    def tearDown(self): self.db.close()
    def test_snapshot_repeat_and_package_source_totals(self):
        ivy=import_snapshot(self.db,self.token,raw())
        self.assertEqual(ivy,import_snapshot(self.db,self.token,raw()))
        pantops=import_snapshot(self.db,self.token,raw("pantops",taxable="2000.00",nontaxable="6000.00",control="8000.00",tax="106.00"))
        key,manifest=prepare(self.db,self.token,[ivy,pantops])
        self.assertEqual(key,prepare(self.db,self.token,[pantops,ivy])[0])
        self.assertEqual(manifest["totals"]["net_sales_control"],"13000.00")
        self.assertEqual(manifest["totals"]["tax_collected"],"159.00")
        self.assertEqual(manifest["status"],"source_reconciled_not_return_ready")
    def test_missing_duplicate_mixed_period_store(self):
        ivy=import_snapshot(self.db,self.token,raw())
        for ids in [[ivy],[ivy,ivy],[ivy,"missing"]]:
            with self.assertRaises(ValueError): prepare(self.db,self.token,ids)
        other=import_snapshot(self.db,self.token,raw("pantops",period="2026-11"))
        with self.assertRaises(ValueError): prepare(self.db,self.token,[ivy,other])
        other=import_snapshot(self.db,self.token,raw(taxable="999.00",control="4999.00"))
        with self.assertRaises(ValueError): prepare(self.db,self.token,[ivy,other])
    def test_schema_and_precision_rejected(self):
        for data in [b"unexpected\n1\n",raw()+b"extra\n",raw(tax="NaN"),raw(tax="1e2"),raw(tax="1.001"),raw(store="unknown"),raw(period="2026-13"),b"x"*65537]:
            with self.subTest(data=data[:60]):
                with self.assertRaises(ValueError): parse(data)
    def test_control_total_and_signed_refunds(self):
        with self.assertRaises(ValueError): parse(raw(control="5000.01"))
        row=parse(raw(taxable="-10.00",nontaxable="0.00",control="-10.00",tax="-0.53"))
        self.assertEqual(row["net_taxable_sales"],"-10.00")
    def test_anonymous_import_denied(self):
        with self.assertRaises(PermissionError): import_snapshot(self.db,"",raw())
    def test_immutable_sources_and_packages(self):
        ivy=import_snapshot(self.db,self.token,raw())
        pantops=import_snapshot(self.db,self.token,raw("pantops"))
        key,_=prepare(self.db,self.token,[ivy,pantops])
        for table,id in [("sales_snapshots",ivy),("preparation_packages",key)]:
            with self.assertRaises(sqlite3.IntegrityError):
                with self.db: self.db.execute("DELETE FROM "+table+" WHERE id=?",(id,))
    def test_corrected_snapshot_preserves_previous_package(self):
        ivy=import_snapshot(self.db,self.token,raw())
        pantops=import_snapshot(self.db,self.token,raw("pantops"))
        old,_=prepare(self.db,self.token,[ivy,pantops])
        revised=import_snapshot(self.db,self.token,raw(taxable="900.00",control="4900.00"))
        new,_=prepare(self.db,self.token,[revised,pantops])
        self.assertNotEqual(old,new)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM preparation_packages").fetchone()[0],2)

    def test_replace_cannot_bypass_immutable_sources_or_packages(self):
        ivy=import_snapshot(self.db,self.token,raw())
        pantops=import_snapshot(self.db,self.token,raw("pantops"))
        package_id,_=prepare(self.db,self.token,[ivy,pantops])
        self.assertEqual(self.db.execute("PRAGMA recursive_triggers").fetchone()[0],1)
        for table,id in [("sales_snapshots",ivy),("preparation_packages",package_id)]:
            with self.assertRaises(sqlite3.IntegrityError):
                with self.db:
                    self.db.execute("INSERT OR REPLACE INTO "+table+" SELECT * FROM "+table+" WHERE id=?",(id,))
            self.assertEqual(self.db.execute("SELECT COUNT(*) FROM "+table+" WHERE id=?",(id,)).fetchone()[0],1)
    def test_revocation_before_import_lock_denies_write(self):
        from unittest.mock import patch
        from complied import imports
        from complied.access import disable_user
        original=imports.authorize
        calls=[]
        def gate(*args):
            user=original(*args)
            if not calls:
                calls.append(1)
                disable_user(self.db,"owner")
            return user
        with patch.object(imports,"authorize",side_effect=gate):
            with self.assertRaises(PermissionError):
                import_snapshot(self.db,self.token,raw())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sales_snapshots").fetchone()[0],0)
    def test_revocation_before_package_lock_denies_write(self):
        from unittest.mock import patch
        from complied import imports
        from complied.access import disable_user
        ids=[import_snapshot(self.db,self.token,raw()),import_snapshot(self.db,self.token,raw("pantops"))]
        original=imports.authorize
        calls=[]
        def gate(*args):
            user=original(*args)
            if not calls:
                calls.append(1)
                disable_user(self.db,"owner")
            return user
        with patch.object(imports,"authorize",side_effect=gate):
            with self.assertRaises(PermissionError): prepare(self.db,self.token,ids)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM preparation_packages").fetchone()[0],0)

    def test_browser_pair_atomic_and_idempotent(self):
        from complied.imports import import_pair
        ivy=raw()
        pantops=raw("pantops")
        key,manifest=import_pair(self.db,self.token,ivy,pantops)
        self.assertEqual(manifest["totals"]["net_sales_control"],"10000.00")
        self.assertEqual(key,import_pair(self.db,self.token,ivy,pantops)[0])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sales_snapshots").fetchone()[0],2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM preparation_packages").fetchone()[0],1)
        with self.assertRaises(ValueError):
            import_pair(self.db,self.token,raw(tax="1.001"),pantops)
        with self.assertRaises(ValueError):
            import_pair(self.db,self.token,raw(),raw("ivy"))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM preparation_packages").fetchone()[0],1)
    def test_browser_pair_revocation_inside_lock(self):
        from unittest.mock import patch
        from complied import imports
        from complied.access import disable_user
        original=imports.authorize
        calls=[]
        def gate(*args):
            user=original(*args)
            if not calls:
                calls.append(1)
                disable_user(self.db,"owner")
            return user
        with patch.object(imports,"authorize",side_effect=gate):
            with self.assertRaises(PermissionError):
                imports.import_pair(self.db,self.token,raw(),raw("pantops"))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sales_snapshots").fetchone()[0],0)
