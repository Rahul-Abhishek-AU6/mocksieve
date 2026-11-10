"""Unit tests for Python source symbol indexing."""
import tempfile
import unittest
from pathlib import Path

from mocksieve.parsers.source_index import SourceSymbolIndex


class TestSourceIndex(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.src = self.root / "src"
        self.src.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_index_modules_classes_functions(self):
        services_dir = self.src / "services"
        services_dir.mkdir()
        (services_dir / "__init__.py").write_text("", encoding="utf-8")
        (services_dir / "billing.py").write_text(
            """
def calculate_tax(amount, rate):
    return amount * rate

class InvoiceService:
    def generate_pdf(self, invoice_id):
        pass

    def send_email(self, recipient):
        pass
""",
            encoding="utf-8"
        )

        idx = SourceSymbolIndex(self.root, source_roots=["src"])
        self.assertIn("services.billing", idx.modules)

        # Resolve top-level function
        found, mod, sym = idx.resolve_target("services.billing.calculate_tax")
        self.assertTrue(found)
        self.assertEqual(mod, "services.billing")
        self.assertEqual(sym, "calculate_tax")

        # Resolve class method
        found, mod, sym = idx.resolve_target("services.billing.InvoiceService.generate_pdf")
        self.assertTrue(found)
        self.assertEqual(sym, "InvoiceService.generate_pdf")

        # Resolve non-existent function
        found, mod, sym = idx.resolve_target("services.billing.old_deleted_func")
        self.assertFalse(found)
        self.assertEqual(mod, "services.billing")
        self.assertEqual(sym, "old_deleted_func")

        # Resolve non-existent method
        found, mod, sym = idx.resolve_target("services.billing.InvoiceService.deleted_method")
        self.assertFalse(found)
        self.assertEqual(sym, "InvoiceService.deleted_method")


if __name__ == "__main__":
    unittest.main()
