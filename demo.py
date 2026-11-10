#!/usr/bin/env python3
"""MockSieve Interactive Simulation Demo.

Simulates a real-world multi-stage developer / AI agent workflow:
1. Baseline codebase with services and unit tests using autospec=True.
2. An AI coding agent refactors source code (renaming calculate_tax -> calculate_invoice_tax).
3. The unit test passes because unconstrained mocks don't validate real symbol existence.
4. MockSieve statically catches the ghost mock target and blocks the CI gate.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mocksieve.cli import main


def run_demo():
    temp_dir = tempfile.TemporaryDirectory()
    demo_root = Path(temp_dir.name)

    print("=" * 60)
    print(" MOCKSIEVE INTERACTIVE DEMO")
    print("=" * 60)

    try:
        # Step 1: Create source module
        print("\n[Step 1] Creating baseline source module (src/services/billing.py):")
        src_dir = demo_root / "src" / "services"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (src_dir / "billing.py").write_text(
            """def calculate_tax(amount: float, rate: float = 0.05) -> float:
    return amount * rate

class InvoiceService:
    def create_invoice(self, amount: float):
        return {"amount": amount, "tax": calculate_tax(amount)}
""",
            encoding="utf-8"
        )
        print("  -> Defined: calculate_tax() and InvoiceService.create_invoice()")

        # Step 2: Create unit tests
        print("\n[Step 2] Authoring unit tests with autospec protection:")
        test_dir = demo_root / "tests"
        test_dir.mkdir()
        (test_dir / "test_billing.py").write_text(
            """from unittest.mock import patch

@patch("services.billing.calculate_tax", autospec=True)
def test_invoice(mock_tax):
    mock_tax.return_value = 5.0
    from services.billing import InvoiceService
    service = InvoiceService()
    inv = service.create_invoice(100.0)
    assert inv["tax"] == 5.0
""",
            encoding="utf-8"
        )
        print("  -> test_billing.py mocks calculate_tax with autospec=True")

        # Step 3: Run baseline audit
        print("\n[Step 3] Running MockSieve on clean baseline:")
        main(["--path", str(demo_root)])

        # Step 4: Simulate AI Agent refactoring source code
        print("\n[Step 4] Simulating AI coding agent refactoring source code:")
        print("  -> Agent renames calculate_tax -> calculate_invoice_tax in src/services/billing.py")
        print("  -> (Agent neglects to update test_billing.py, leaving stale @patch target)")
        (src_dir / "billing.py").write_text(
            """def calculate_invoice_tax(amount: float, rate: float = 0.05) -> float:
    return amount * rate

class InvoiceService:
    def create_invoice(self, amount: float):
        return {"amount": amount, "tax": calculate_invoice_tax(amount)}
""",
            encoding="utf-8"
        )

        # Step 5: Run MockSieve catching ghost mock target
        print("\n[Step 5] Running MockSieve before PR merge / CI gate:")
        exit_code = main([
            "--path", str(demo_root),
            "--output-json", str(demo_root / "mock-report.json"),
            "--output-md", str(demo_root / "mock-report.md")
        ])
        print(f"  -> MockSieve exited with code: {exit_code} (1 indicates blocked CI gate)")

        # Step 6: Review generated Markdown card
        print("\n[Step 6] Generated Markdown review card (mock-report.md):")
        print("-" * 50)
        print((demo_root / "mock-report.md").read_text(encoding="utf-8"))
        print("-" * 50)

    finally:
        temp_dir.cleanup()

    print("\nDemo completed successfully!")


if __name__ == "__main__":
    run_demo()
