"""Core reconciliation engine for MockSieve."""
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from .parsers.source_index import SourceSymbolIndex, build_source_index
from .parsers.test_parser import MockTargetFinding, extract_mock_findings

DEFAULT_IGNORE_DIRS = {
    ".git", ".hg", "venv", ".venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", "assets",
    "logs", "prompts", "reports"
}


@dataclass
class GhostMockViolation:
    target_string: str
    file_path: str
    line_number: int
    raw_statement: str
    module_name: str
    symbol_name: str
    reason: str


@dataclass
class UnconstrainedMockWarning:
    target_string: str
    file_path: str
    line_number: int
    raw_statement: str
    remediation: str


@dataclass
class MockSieveReport:
    root_dir: str
    is_diff_mode: bool
    indexed_modules_count: int
    scanned_test_files_count: int
    total_mock_targets: int
    ghost_mocks: List[GhostMockViolation] = field(default_factory=list)
    unconstrained_mocks: List[UnconstrainedMockWarning] = field(default_factory=list)
    healthy_mocks_count: int = 0

    @property
    def has_critical_violations(self) -> bool:
        return len(self.ghost_mocks) > 0


class MockSieveAuditor:
    def __init__(self, root_dir: Path | str, diff_mode: bool = False, base_ref: Optional[str] = None):
        self.root_dir = Path(root_dir).resolve()
        self.diff_mode = diff_mode
        self.base_ref = base_ref
        self.source_index = build_source_index(self.root_dir)

    def _get_target_test_files(self) -> List[Path]:
        if self.diff_mode:
            return self._get_diff_test_files()
        return self._crawl_test_files()

    def _get_diff_test_files(self) -> List[Path]:
        cmd = ["git", "diff", "--name-only"]
        if self.base_ref:
            cmd.append(self.base_ref)
        else:
            cmd.append("HEAD")

        try:
            res = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                res = subprocess.run(["git", "diff", "--name-only"], cwd=self.root_dir, capture_output=True, text=True, check=False)

            output = res.stdout.strip().splitlines()
            files = []
            for line in output:
                p = (self.root_dir / line.strip()).resolve()
                if p.is_file() and self._is_test_file(p):
                    files.append(p)
            if not files:
                status_res = subprocess.run(["git", "status", "--porcelain"], cwd=self.root_dir, capture_output=True, text=True, check=False)
                for line in status_res.stdout.splitlines():
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        p = (self.root_dir / parts[1].strip()).resolve()
                        if p.is_file() and self._is_test_file(p):
                            files.append(p)
            return files
        except Exception:
            return self._crawl_test_files()

    def _crawl_test_files(self) -> List[Path]:
        test_files = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS and not d.startswith(".")]
            for fname in files:
                p = Path(root) / fname
                if self._is_test_file(p):
                    test_files.append(p)
        return sorted(test_files)

    def _is_test_file(self, path: Path) -> bool:
        if not path.suffix == ".py":
            return False
        name = path.name
        return name.startswith("test_") or name.endswith("_test.py") or "tests" in path.parts

    def audit(self) -> MockSieveReport:
        test_files = self._get_target_test_files()
        report = MockSieveReport(
            root_dir=str(self.root_dir),
            is_diff_mode=self.diff_mode,
            indexed_modules_count=len(self.source_index.modules),
            scanned_test_files_count=len(test_files),
            total_mock_targets=0,
        )

        for tfile in test_files:
            rel_path = str(tfile.relative_to(self.root_dir))
            findings = extract_mock_findings(tfile)
            report.total_mock_targets += len(findings)

            for f in findings:
                if f.is_patch_object:
                    # patch.object(Class, "method")
                    # Check if class exists in any indexed module and if method is present
                    resolved_cls = False
                    for mod in self.source_index.modules.values():
                        if f.class_name in mod.classes:
                            resolved_cls = True
                            cls_sym = mod.classes[f.class_name]
                            if f.attribute_name not in cls_sym.methods:
                                report.ghost_mocks.append(
                                    GhostMockViolation(
                                        target_string=f.target_string,
                                        file_path=rel_path,
                                        line_number=f.line_number,
                                        raw_statement=f.raw_statement,
                                        module_name=mod.module_dotted_path,
                                        symbol_name=f.attribute_name or "",
                                        reason=f"Class '{f.class_name}' does not have method '{f.attribute_name}'",
                                    )
                                )
                            break
                    if not f.has_autospec:
                        report.unconstrained_mocks.append(
                            UnconstrainedMockWarning(
                                target_string=f.target_string,
                                file_path=rel_path,
                                line_number=f.line_number,
                                raw_statement=f.raw_statement,
                                remediation=f"Add autospec=True to patch.object({f.class_name}, '{f.attribute_name}')",
                            )
                        )
                    else:
                        report.healthy_mocks_count += 1
                    continue

                # Standard patch("target.string")
                found, mod_path, sym_name = self.source_index.resolve_target(f.target_string)

                if mod_path and not found:
                    # Module was found in source index, but the symbol is missing!
                    report.ghost_mocks.append(
                        GhostMockViolation(
                            target_string=f.target_string,
                            file_path=rel_path,
                            line_number=f.line_number,
                            raw_statement=f.raw_statement,
                            module_name=mod_path,
                            symbol_name=sym_name or "",
                            reason=f"Symbol '{sym_name}' does not exist in module '{mod_path}'",
                        )
                    )
                elif found:
                    # Target exists in local codebase
                    if not f.has_autospec:
                        report.unconstrained_mocks.append(
                            UnconstrainedMockWarning(
                                target_string=f.target_string,
                                file_path=rel_path,
                                line_number=f.line_number,
                                raw_statement=f.raw_statement,
                                remediation=f"Add autospec=True to patch('{f.target_string}')",
                            )
                        )
                    else:
                        report.healthy_mocks_count += 1
                else:
                    # Third-party or external module (e.g. requests.get, os.environ)
                    if not f.has_autospec:
                        report.unconstrained_mocks.append(
                            UnconstrainedMockWarning(
                                target_string=f.target_string,
                                file_path=rel_path,
                                line_number=f.line_number,
                                raw_statement=f.raw_statement,
                                remediation=f"Consider autospec=True on external patch('{f.target_string}')",
                            )
                        )
                    else:
                        report.healthy_mocks_count += 1

        return report


def audit_mock_drift(root_dir: Path | str, diff_mode: bool = False, base_ref: Optional[str] = None) -> MockSieveReport:
    auditor = MockSieveAuditor(root_dir, diff_mode=diff_mode, base_ref=base_ref)
    return auditor.audit()
