"""Unit tests for test file mock extractor."""
import tempfile
import unittest
from pathlib import Path

from mocksieve.parsers.test_parser import extract_mock_findings


class TestTestParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_patch_decorators_and_context_managers(self):
        tfile = self.root / "test_sample.py"
        tfile.write_text(
            """from unittest.mock import patch

@patch("services.billing.calculate_tax", autospec=True)
@patch("services.billing.old_func")
def test_calc(mock_old, mock_tax):
    with patch("services.mailer.send_email", autospec=True) as mock_mail:
        mock_mail()

def test_object():
    with patch.object(InvoiceService, "generate_pdf") as m:
        pass
""",
            encoding="utf-8"
        )

        findings = extract_mock_findings(tfile)
        self.assertEqual(len(findings), 4)

        # Check targets and autospec
        target_map = {f.target_string: f.has_autospec for f in findings}
        self.assertTrue(target_map["services.billing.calculate_tax"])
        self.assertFalse(target_map["services.billing.old_func"])
        self.assertTrue(target_map["services.mailer.send_email"])
        self.assertFalse(target_map["InvoiceService.generate_pdf"])


if __name__ == "__main__":
    unittest.main()
