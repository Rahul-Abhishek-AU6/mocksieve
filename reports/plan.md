# Plan: MockSieve — Zero-Dependency Mock Drift & Stale Test Double Gate

Date: 2026-11-11 (IST)  
Stage: Plan  
Project: **MockSieve**

---

## 1. Success Metrics

1. **Ghost Target Detection**: 100% detection of `@patch("...")` calls targeting functions, classes, or attributes that do not exist in the source codebase.
2. **Unconstrained Mock Identification**: 100% detection of bare `@patch` decorators that omit `autospec=True` or `spec=...`.
3. **Execution Latency**: Scans a 1,000-line test suite in < 40ms, making it suitable for instantaneous git pre-commit hooks and CI gates.
4. **Zero Configuration**: Automatically discovers source roots (`src/`, `app/`, `lib/`, or project root) and test directories (`tests/`, `test/`).
5. **Deterministic Exit Codes**: Returns code 1 when ghost mock targets or unconstrained mocks are detected; returns code 0 when clean.

---

## 2. Minimal Architecture

Directory structure inside `projects/20261111-022336-developer-and-engineering-pain-points`:

```
src/
└── mocksieve/
    ├── __init__.py          # Version and top-level exports
    ├── __main__.py          # python -m mocksieve
    ├── cli.py               # Argument parser and exit code coordination
    ├── core.py              # Audit engine reconciling test mocks vs source symbols
    ├── parsers/
    │   ├── __init__.py
    │   ├── test_parser.py   # AST visitor extracting patch decorators, context managers, and mock calls
    │   └── source_index.py  # AST indexer cataloging defined modules, classes, and functions
    └── reporter.py          # ANSI terminal receipts, JSON reports, Markdown PR review cards
```

---

## 3. Local/Free Dependency Inventory

- **Runtime**: Pure Python 3.10+ standard library (`ast`, `re`, `pathlib`, `json`, `argparse`, `sys`, `subprocess`, `os`).
- **Zero Third-Party Packages**: No `pip install` required.
- **Offline & Private**: Never executes test code or source files; purely static AST inspection.

---

## 4. Security & Privacy Notes

- Static inspection only: never imports user modules or invokes `eval()`/`exec()`.
- Safe against untrusted or buggy code: parses code purely as Abstract Syntax Trees.
- No network access or external telemetry.

---

## 5. Task Breakdown

1. **Source Indexer (`source_index.py`)**:
   - Recursively traverses source directory.
   - For every `.py` file, parses AST to index all top-level functions, classes, and methods, plus module import aliases.
2. **Test Parser (`test_parser.py`)**:
   - AST visitor identifying:
     - `@patch("target.string", ...)`
     - `with patch("target.string", ...):`
     - `patch.object(TargetClass, "method", ...)`
     - Checks if `autospec=True` or `spec=...` keyword arguments are present.
3. **Core Reconciliation Engine (`core.py`)**:
   - Resolves target string (e.g. `services.billing.calculate_tax`) against indexed source files.
   - Categorizes findings:
     - 🚨 **GHOST MOCK**: Target symbol does not exist in the target module.
     - ⚠️ **UNCONSTRAINED MOCK**: Patch omits `autospec=True` (risk of false passes on typos and signature changes).
4. **CLI & Reporters (`cli.py`, `reporter.py`)**:
   - Terminal summary with clean ANSI colors.
   - Machine-readable JSON output (`--output-json`).
   - Markdown PR review card (`--output-md`).
   - `--diff` flag for checking only modified files in git working tree.
5. **Test Suite (`tests/`)**:
   - Tests for AST target extraction, source indexing, ghost detection, and CLI exit codes.
6. **Documentation & Demo**:
   - `README.md`, MIT `LICENSE`, and runnable `demo.py`.
7. **Visual Assets**:
   - Invoke `image-generator` subagent for conceptual architecture visual.
   - Produce truthful terminal SVG cassette.

---

## 6. Executable Acceptance Tests

1. **Ghost Mock Target Detection**:
   - Given a test with `@patch("myapp.services.old_deleted_func")` where `old_deleted_func` is not in `myapp/services.py`.
   - Result: Flagged as GHOST MOCK, exit code 1.
2. **Unconstrained Mock Warning**:
   - Given a test with `@patch("myapp.services.real_func")` lacking `autospec=True`.
   - Result: Flagged as UNCONSTRAINED MOCK.
3. **Clean Autospec Mock**:
   - Given a test with `@patch("myapp.services.real_func", autospec=True)`.
   - Result: Validated as honest mock, clean pass, exit code 0.
4. **Method Patch Detection**:
   - Given a test with `@patch.object(RealClass, "deleted_method")`.
   - Result: Flagged as missing method on class.
