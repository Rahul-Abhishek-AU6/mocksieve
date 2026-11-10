"""Source code symbol indexer using Python AST."""
import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class FunctionSignature:
    name: str
    params: List[str]
    has_varargs: bool = False
    has_varkw: bool = False


@dataclass
class ClassSymbol:
    name: str
    methods: Dict[str, FunctionSignature] = field(default_factory=dict)


@dataclass
class ModuleSymbol:
    module_dotted_path: str
    file_path: str
    functions: Dict[str, FunctionSignature] = field(default_factory=dict)
    classes: Dict[str, ClassSymbol] = field(default_factory=dict)
    imported_names: Set[str] = field(default_factory=set)

    def has_symbol(self, name: str) -> bool:
        return (
            name in self.functions
            or name in self.classes
            or name in self.imported_names
        )


class SourceVisitor(ast.NodeVisitor):
    def __init__(self, module_dotted_path: str, file_path: str):
        self.module = ModuleSymbol(module_dotted_path=module_dotted_path, file_path=file_path)
        self.current_class: Optional[ClassSymbol] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.current_class
        cls_sym = ClassSymbol(name=node.name)
        self.module.classes[node.name] = cls_sym
        self.current_class = cls_sym
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_function(node)
        self.generic_visit(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        params = [a.arg for a in node.args.args]
        sig = FunctionSignature(
            name=node.name,
            params=params,
            has_varargs=node.args.vararg is not None,
            has_varkw=node.args.kwarg is not None,
        )
        if self.current_class:
            self.current_class.methods[node.name] = sig
        else:
            self.module.functions[node.name] = sig

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            as_name = alias.asname or alias.name
            self.module.imported_names.add(as_name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            as_name = alias.asname or alias.name
            self.module.imported_names.add(as_name)
        self.generic_visit(node)


class SourceSymbolIndex:
    def __init__(self, root_dir: Path | str, source_roots: Optional[List[str]] = None):
        self.root_dir = Path(root_dir).resolve()
        self.source_roots = source_roots or ["src", "app", "lib", "."]
        self.modules: Dict[str, ModuleSymbol] = {}
        self.build_index()

    def _file_to_dotted_path(self, file_path: Path, source_root: Path) -> str:
        try:
            rel = file_path.relative_to(source_root)
        except ValueError:
            return ""

        parts = list(rel.parts)
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        if parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)

    def build_index(self):
        visited_files: Set[Path] = set()

        for sroot_name in self.source_roots:
            sroot = (self.root_dir / sroot_name).resolve()
            if not sroot.is_dir():
                continue

            for root, dirs, files in os.walk(sroot):
                # Prune common ignore folders
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in {"tests", "test", "venv", ".venv", "__pycache__", "build", "dist", "node_modules"}
                ]
                for fname in files:
                    if fname.endswith(".py") and not fname.startswith("test_"):
                        p = Path(root) / fname
                        if p in visited_files:
                            continue
                        visited_files.add(p)

                        dotted = self._file_to_dotted_path(p, sroot)
                        if not dotted:
                            continue

                        try:
                            content = p.read_text(encoding="utf-8", errors="replace")
                            tree = ast.parse(content, filename=str(p))
                            visitor = SourceVisitor(dotted, str(p))
                            visitor.visit(tree)
                            self.modules[dotted] = visitor.module
                            # Also register under root-relative dotted path if different
                            root_rel_dotted = self._file_to_dotted_path(p, self.root_dir)
                            if root_rel_dotted and root_rel_dotted != dotted:
                                self.modules[root_rel_dotted] = visitor.module
                        except Exception:
                            continue

    def resolve_target(self, target_string: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Resolve a dotted target like 'services.billing.calculate_tax'.

        Returns: (found: bool, module_path: Optional[str], symbol_name: Optional[str])
        """
        parts = target_string.split(".")
        if len(parts) < 2:
            return False, None, None

        # Check progressively: e.g. 'services.billing' -> 'calculate_tax'
        for i in range(len(parts) - 1, 0, -1):
            mod_candidate = ".".join(parts[:i])
            symbol_candidate = parts[i]
            rest = parts[i + 1:]

            if mod_candidate in self.modules:
                mod = self.modules[mod_candidate]
                if not rest:
                    # Target is a function, class, or re-exported name in module
                    if mod.has_symbol(symbol_candidate):
                        return True, mod_candidate, symbol_candidate
                    return False, mod_candidate, symbol_candidate
                elif len(rest) == 1:
                    # Target is Class.method e.g. 'BillingService.calculate_tax'
                    if symbol_candidate in mod.classes:
                        cls_sym = mod.classes[symbol_candidate]
                        if rest[0] in cls_sym.methods:
                            return True, mod_candidate, f"{symbol_candidate}.{rest[0]}"
                        return False, mod_candidate, f"{symbol_candidate}.{rest[0]}"

        return False, None, None


def build_source_index(root_dir: Path | str) -> SourceSymbolIndex:
    return SourceSymbolIndex(root_dir)
