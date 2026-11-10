"""MockSieve: Zero-dependency mock drift and stale test double detector."""

__version__ = "0.1.0"
__all__ = ["MockSieveAuditor", "MockSieveReport", "audit_mock_drift"]

from .core import MockSieveAuditor, MockSieveReport, audit_mock_drift
