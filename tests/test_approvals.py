import sys
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from complied.approvals import Approval, Package, Purpose, may_execute

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.package = Package("demo", "VA", "2026-09", "v1", Decimal("123.45"), "synthetic-portal")
        self.approval = Approval(self.package, Purpose.FILING, "owner-demo")
    def allowed(self, package=None, approval=None, purpose=Purpose.FILING, **options):
        defaults = dict(adapter_verified=True, unresolved_exceptions=0)
        defaults.update(options)
        return may_execute(package or self.package, approval or self.approval, purpose, **defaults)
    def test_exact_filing_approval(self):
        self.assertTrue(self.allowed())
    def test_filing_does_not_approve_payment(self):
        self.assertFalse(self.allowed(purpose=Purpose.PAYMENT))
    def test_material_changes_invalidate_approval(self):
        for field, value in dict(entity="other", jurisdiction="MD", period="2026-10", version="v2", amount=Decimal("124"), destination="other").items():
            with self.subTest(field=field):
                self.assertFalse(self.allowed(package=replace(self.package, **{field:value})))
    def test_execution_gates(self):
        for option in [dict(adapter_verified=False), dict(unresolved_exceptions=1), dict(outcome_unknown=True)]:
            self.assertFalse(self.allowed(**option))
    def test_missing_approval(self):
        self.assertFalse(may_execute(self.package, None, Purpose.FILING, adapter_verified=True, unresolved_exceptions=0))
    def test_revoked_or_anonymous_approval(self):
        self.assertFalse(self.allowed(approval=replace(self.approval, revoked=True)))
        self.assertFalse(self.allowed(approval=replace(self.approval, actor="")))
    def test_separate_payment_approval(self):
        self.assertTrue(self.allowed(approval=replace(self.approval, purpose=Purpose.PAYMENT), purpose=Purpose.PAYMENT))
