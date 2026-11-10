"""Reporters for MockSieve: Terminal output, JSON serialization, and Markdown cards."""
import json
import os
import sys
from typing import Optional, TextIO
from .core import MockSieveReport


def use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


class Color:
    RED = "\033[91m" if use_color() else ""
    GREEN = "\033[92m" if use_color() else ""
    YELLOW = "\033[93m" if use_color() else ""
    BLUE = "\033[94m" if use_color() else ""
    MAGENTA = "\033[95m" if use_color() else ""
    CYAN = "\033[96m" if use_color() else ""
    BOLD = "\033[1m" if use_color() else ""
    DIM = "\033[2m" if use_color() else ""
    RESET = "\033[0m" if use_color() else ""


def print_terminal_summary(report: MockSieveReport, stream: Optional[TextIO] = None) -> None:
    if stream is None:
        stream = sys.stdout

    print(f"\n{Color.BOLD}{Color.CYAN}MockSieve Mock Drift & Test Double Audit{Color.RESET}", file=stream)
    print(f"{Color.DIM}Root: {report.root_dir} | Mode: {'Git Diff' if report.is_diff_mode else 'Full Workspace'}{Color.RESET}", file=stream)
    print(f"{Color.DIM}Indexed {report.indexed_modules_count} source modules | Scanned {report.scanned_test_files_count} test files ({report.total_mock_targets} mock targets){Color.RESET}\n", file=stream)

    # 1. Ghost mocks
    if report.ghost_mocks:
        print(f"{Color.BOLD}{Color.RED}🚨 GHOST MOCK TARGETS DETECTED ({len(report.ghost_mocks)}){Color.RESET}", file=stream)
        print(f"{Color.DIM}These mocks target functions/attributes that do not exist in the source code! Tests may pass while production fails!{Color.RESET}\n", file=stream)
        for idx, g in enumerate(report.ghost_mocks, start=1):
            print(f"  {Color.BOLD}{idx}. {Color.RED}'{g.target_string}'{Color.RESET} at {Color.BOLD}{g.file_path}:{g.line_number}{Color.RESET}", file=stream)
            print(f"     {Color.DIM}Statement:{Color.RESET} {g.raw_statement}", file=stream)
            print(f"     {Color.YELLOW}Reason:{Color.RESET} {g.reason}", file=stream)
            print("", file=stream)
    else:
        print(f"{Color.BOLD}{Color.GREEN}✅ No ghost mock targets detected.{Color.RESET} All patched symbols exist in source files.\n", file=stream)

    # 2. Unconstrained mocks
    if report.unconstrained_mocks:
        print(f"{Color.BOLD}{Color.YELLOW}⚠️  UNCONSTRAINED MOCKS (MISSING AUTOSPEC) ({len(report.unconstrained_mocks)}){Color.RESET}", file=stream)
        print(f"{Color.DIM}Bare mocks act as 'infinite yes-men'. They silently accept renamed methods, typos, and invalid argument counts.{Color.RESET}\n", file=stream)
        for u in report.unconstrained_mocks:
            print(f"  - {Color.YELLOW}{u.target_string}{Color.RESET} at {u.file_path}:{u.line_number} -> {u.remediation}", file=stream)
        print("", file=stream)

    # Verdict
    if report.has_critical_violations:
        print(f"{Color.BOLD}{Color.RED}Result: FAILED{Color.RESET} — Found {len(report.ghost_mocks)} ghost mock target(s).\n", file=stream)
    else:
        print(f"{Color.BOLD}{Color.GREEN}Result: PASSED{Color.RESET} — Test mock integrity verified ({report.healthy_mocks_count} healthy mocks).\n", file=stream)


def to_dict(report: MockSieveReport) -> dict:
    return {
        "status": "failed" if report.has_critical_violations else "passed",
        "root_dir": report.root_dir,
        "is_diff_mode": report.is_diff_mode,
        "indexed_modules_count": report.indexed_modules_count,
        "scanned_test_files_count": report.scanned_test_files_count,
        "total_mock_targets": report.total_mock_targets,
        "healthy_mocks_count": report.healthy_mocks_count,
        "ghost_mocks": [
            {
                "target_string": g.target_string,
                "file_path": g.file_path,
                "line_number": g.line_number,
                "raw_statement": g.raw_statement,
                "module_name": g.module_name,
                "symbol_name": g.symbol_name,
                "reason": g.reason,
            }
            for g in report.ghost_mocks
        ],
        "unconstrained_mocks": [
            {
                "target_string": u.target_string,
                "file_path": u.file_path,
                "line_number": u.line_number,
                "raw_statement": u.raw_statement,
                "remediation": u.remediation,
            }
            for u in report.unconstrained_mocks
        ],
    }


def to_json(report: MockSieveReport, indent: int = 2) -> str:
    return json.dumps(to_dict(report), indent=indent)


def to_markdown(report: MockSieveReport) -> str:
    lines = [
        "# MockSieve Verification Report",
        "",
        f"- **Status**: {'🔴 **FAILED**' if report.has_critical_violations else '🟢 **PASSED**'}",
        f"- **Mode**: `{'git-diff' if report.is_diff_mode else 'full-workspace'}`",
        f"- **Indexed Source Modules**: `{report.indexed_modules_count}`",
        f"- **Scanned Test Files**: `{report.scanned_test_files_count}`",
        f"- **Total Mock Targets**: `{report.total_mock_targets}`",
        f"- **Healthy Autospec Mocks**: `{report.healthy_mocks_count}`",
        "",
    ]

    if report.ghost_mocks:
        lines.append("### 🚨 Ghost Mock Targets (Symbol Deleted / Renamed in Source)")
        lines.append("")
        lines.append("| Mock Target | Test Location | Defect Reason |")
        lines.append("|---|---|---|")
        for g in report.ghost_mocks:
            lines.append(f"| `{g.target_string}` | `{g.file_path}:{g.line_number}` | {g.reason} |")
        lines.append("")

    if report.unconstrained_mocks:
        lines.append("### ⚠️ Unconstrained Mocks (Missing `autospec=True`)")
        lines.append("")
        lines.append("| Target | Location | Suggested Action |")
        lines.append("|---|---|---|")
        for u in report.unconstrained_mocks:
            lines.append(f"| `{u.target_string}` | `{u.file_path}:{u.line_number}` | `{u.remediation}` |")
        lines.append("")

    if not report.ghost_mocks and not report.unconstrained_mocks:
        lines.append("✨ **All test mocks target existing source symbols with autospec protection!**")
        lines.append("")

    return "\n".join(lines)
