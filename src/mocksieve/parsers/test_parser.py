"""Test file parser extracting mock patch targets and autospec configurations."""
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class MockTargetFinding:
    target_string: str
    file_path: str
    line_number: int
    raw_statement: str
    has_autospec: bool
    is_patch_object: bool = False
    class_name: Optional[str] = None
    attribute_name: Optional[str] = None


class TestMockVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.findings: List[MockTargetFinding] = []

    def _get_raw_line(self, lineno: int) -> str:
        idx = max(0, lineno - 1)
        return self.source_lines[idx].strip() if idx < len(self.source_lines) else ""

    def visit_Call(self, node: ast.Call):
        # Checks patch("target") or patch.object(...) in decorators, 'with' blocks, or expressions
        self._inspect_patch_call(node)
        self.generic_visit(node)

    def _has_autospec(self, node: ast.Call) -> bool:
        for kw in node.keywords:
            if kw.arg in {"autospec", "spec"} and not (
                isinstance(kw.value, ast.Constant) and kw.value.value is False
            ):
                return True
        return False

    def _inspect_patch_call(self, node: ast.Call):
        func = node.func
        is_patch = False
        is_patch_object = False

        if isinstance(func, ast.Name) and func.id in {"patch", "mock_patch"}:
            is_patch = True
        elif isinstance(func, ast.Attribute):
            if func.attr == "patch":
                is_patch = True
            elif func.attr == "object" and isinstance(func.value, ast.Name) and func.value.id == "patch":
                is_patch_object = True

        has_autospec = self._has_autospec(node)

        if is_patch and len(node.args) >= 1:
            target_str = self._extract_string_literal(node.args[0])
            if target_str:
                self.findings.append(
                    MockTargetFinding(
                        target_string=target_str,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        raw_statement=self._get_raw_line(node.lineno),
                        has_autospec=has_autospec,
                        is_patch_object=False,
                    )
                )

        elif is_patch_object and len(node.args) >= 2:
            cls_name = ""
            if isinstance(node.args[0], ast.Name):
                cls_name = node.args[0].id
            attr_name = self._extract_string_literal(node.args[1])
            if cls_name and attr_name:
                self.findings.append(
                    MockTargetFinding(
                        target_string=f"{cls_name}.{attr_name}",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        raw_statement=self._get_raw_line(node.lineno),
                        has_autospec=has_autospec,
                        is_patch_object=True,
                        class_name=cls_name,
                        attribute_name=attr_name,
                    )
                )

    def _extract_string_literal(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if hasattr(ast, "Str") and isinstance(node, ast.Str):
            return node.s
        return None


def extract_mock_findings(file_path: Path | str) -> List[MockTargetFinding]:
    """Parse a test file and extract all mock patch findings."""
    p = Path(file_path)
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    try:
        tree = ast.parse(content, filename=str(p))
    except (SyntaxError, ValueError):
        return []

    lines = content.splitlines()
    visitor = TestMockVisitor(str(p), lines)
    visitor.visit(tree)
    return visitor.findings
