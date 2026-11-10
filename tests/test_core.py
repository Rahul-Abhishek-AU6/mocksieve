"""Integration tests for MockSieve core reconciliation engine."""
import tempfile
import unittest
from pathlib import Path

from mocksieve.core import MockSieveAuditor


class TestCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.src = self.root / "src"
        self.src.mkdir()
        self.tests = self.root / "tests"
        self.tests.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ghost_mock_target_detected(self):
        # Source file with only calculate_tax
        (self.src / "billing.py").write_text(
            "def calculate_tax(amount): return amount * 0.1\n",
            encoding="utf-8"
        )

        # Test file mocks calculate_tax (ok) and old_deleted_tax (ghost!)
        (self.tests / "test_billing.py").write_text(
            """from unittest.mock import patch

@patch("billing.calculate_tax", autospec=True)
def test_valid(m): pass

@patch("billing.old_deleted_tax", autospec=True)
def test_ghost(m): pass
""",
            encoding="utf-8"
        )

        auditor = MockSieveAuditor(self.root)
        report = auditor.audit()

        self.assertTrue(report.has_critical_violations)
        self.assertEqual(len(report.ghost_mocks), 1)
        self.assertEqual(report.ghost_mocks[0].target_string, "billing.old_deleted_tax")
        self.assertEqual(report.healthy_mocks_count, 1)

    def test_unconstrained_mock_warning(self):
        (self.src / "auth.py").write_text(
            "def verify_token(token): return True\n",
            encoding="utf-8"
        )

        # Bare patch without autospec=True
        (self.tests / "test_auth.py").write_text(
            """from unittest.mock import patch

@patch("auth.verify_token")
def test_auth(m): pass
""",
            encoding="utf-8"
        )

        auditor = MockSieveAuditor(self.root)
        report = auditor.audit()

        self.assertFalse(report.has_critical_violations)
        self.assertEqual(len(report.ghost_mocks), 0)
        self.assertEqual(len(report.unconstrained_mocks), 1)
        self.assertEqual(report.unconstrained_mocks[0].target_string, "auth.verify_token")

    def test_clean_autospec_suite_passes(self):
        (self.src / "mailer.py").write_text(
            "def send(recipient, body): pass\n",
            encoding="utf-8"
        )
        (self.tests / "test_mailer.py").write_text(
            """from unittest.mock import patch

@patch("mailer.send", autospec=True)
def test_mail(m): pass
""",
            encoding="utf-8"
        )

        auditor = MockSieveAuditor(self.root)
        report = auditor.audit()

        self.assertFalse(report.has_critical_violations)
        self.assertEqual(len(report.ghost_mocks), 0)
        self.assertEqual(len(report.unconstrained_mocks), 0)
        self.assertEqual(report.healthy_mocks_count, 1)

    def test_patch_object_deleted_method_detected(self):
        (self.src / "payment.py").write_text(
            """class PaymentGateway:
    def charge(self, amount): pass
""",
            encoding="utf-8"
        )
        (self.tests / "test_payment.py").write_text(
            """from unittest.mock import patch
from payment import PaymentGateway

def test_charge():
    with patch.object(PaymentGateway, "old_refund_method", autospec=True):
        pass
""",
            encoding="utf-8"
        )

        auditor = MockSieveAuditor(self.root)
        report = auditor.audit()

        self.assertTrue(report.has_critical_violations)
        self.assertEqual(len(report.ghost_mocks), 1)
        self.assertIn("old_refund_method", report.ghost_mocks[0].reason)


if __name__ == "__main__":
    unittest.main()
