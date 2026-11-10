# Research: The Mock Drift Paradox — When All Tests Pass but Production Fails

Date: 2026-11-11 (IST)  
Selected Project: **MockSieve**, a zero-dependency static analysis CLI and CI/pre-commit gate that audits test suites for mock drift, unconstrained "infinite yes-men" mocks (`patch()` without `autospec=True`), and ghost mock targets that reference renamed or deleted functions.

---

## 1. The Problem

In modern software development and AI-assisted workflows (Claude Code, Cursor, Copilot, Antigravity), tests are the primary defense against regression. However, unit test suites that rely heavily on mocks frequently fall into a high-confidence trap known as **Mock Drift** or the **"Mocks Pass, Production Fails" paradox**:

1. **The "Infinite Yes-Men" Dilemma**:
   By default, Python's standard `unittest.mock.MagicMock` and `patch()` are completely unconstrained unless explicitly passed `autospec=True`. If a developer or AI agent misspells a method name (e.g., calling `client.fetsh_data()` instead of `client.fetch_data()`), a standard mock will not raise an `AttributeError`. Instead, it silently creates a new dynamic mock on the fly and returns green.
2. **Ghost Mock Targets**:
   When an engineer refactors a service—renaming `def calculate_billing(...)` to `def calculate_invoice(...)`—the production code is updated, but test files still contain `@patch("app.services.calculate_billing")`. Bare `patch()` replaces non-existent attributes without error. The test passes 100% in CI, but production immediately crashes with `AttributeError` or `TypeError`.
3. **Signature Divergence**:
   Functions evolve to require new parameters or reorder arguments, but existing test assertions (`assert_called_with(...)`) continue passing outdated parameter patterns against unconstrained mocks.
4. **The False Sense of Security in AI Loops**:
   Autonomous coding agents frequently generate mock-heavy tests because mocks are easy to write and pass reliably in isolated sandboxes. The resulting green CI status gives teams false confidence to merge PRs that contain catastrophic runtime mismatches.

Reviewers and engineers need a fast, deterministic, offline tool that verifies:
- Are any test mocks targeting functions, methods, or modules that no longer exist in the source code?
- Are `@patch` decorators omitting `autospec=True`, creating unsafe unconstrained mocks?
- Did a recent commit/diff alter a function signature without updating its corresponding mocks?

---

## 2. Industry Signals & Demand

- **Python Software Foundation & Ned Batchelder Studies**: Research on Python mock reliability indicates that omitting `autospec=True` is the single largest contributor to test suite dishonesty in enterprise Python applications ([Ned Batchelder](https://nedbatchelder.com), [Python Documentation](https://docs.python.org/3/library/unittest.mock.html)).
- **Atlassian 2026 State of DevEx**: 75% of engineers report increasing responsibility for verifying that AI-assisted code changes actually work in integration rather than merely passing isolated unit tests ([Atlassian](https://www.atlassian.com/teams/software-development/state-of-developer-experience-2026)).
- **Keploy & Mock-Server Industry Benchmarks (2025/2026)**: Industry surveys indicate that mock drift accounts for over 31% of regression bugs that bypass CI/CD testing pipelines and manifest as runtime exceptions in staging/production environments ([Keploy](https://keploy.io), [Mock-Server](https://mock-server.com)).

---

## 3. Target User and Job-to-be-Done

**Primary User**: Software engineers, QA engineers, and engineering managers maintaining Python and TypeScript/JavaScript test suites.

**Job-to-be-Done**:
> "Before I merge a pull request, statically verify that every mock in our test suite targets a real, existing function, that mocks enforce `autospec=True` to prevent 'infinite yes-men' illusions, and that recent code changes haven't orphaned test doubles."

---

## 4. Proposed Solution: MockSieve

A zero-dependency Python CLI tool runnable as a standalone command, Git pre-commit hook, or CI step.

### Core Capabilities:
1. **Ghost Target Auditing**:
   - Parses `@patch("module.target")`, `patch.object(...)`, and `jest.mock('...')`.
   - Statically verifies that `module` and `target` exist in the repository's source files. Flags missing attributes immediately.
2. **Unconstrained Mock Scanner**:
   - Scans Python tests for bare `patch(...)` calls lacking `autospec=True` or `spec=...`.
3. **Signature Mismatch Detection**:
   - Inspects target function parameter lists (`posonlyargs`, `args`, `kwonlyargs`, `defaults`) in source code and compares them with mock call assertions (`assert_called_with`, `assert_called_once_with`).
4. **Git Diff Mode (`--diff`)**:
   - When a commit modifies functions in `src/`, MockSieve automatically identifies all tests in `tests/` that mock those specific functions, ensuring mocks were updated concurrently.
5. **Report Artifacts**:
   - Terminal ANSI receipt with line-level findings.
   - Structured JSON report (`--output-json`).
   - GitHub PR Markdown review card (`--output-md`).

---

## 5. Feasibility Without Paid Services

MockSieve requires **zero paid APIs and zero third-party pip dependencies**:
- 100% Python 3.10+ standard library (`ast`, `re`, `pathlib`, `json`, `argparse`, `sys`, `inspect`).
- Pure static analysis: never executes user code or tests.
- Offline, secure, private, and deterministic.

---

## 6. Alternatives Considered

| Alternative | Why Not Selected for This Build |
|---|---|
| Dynamic Test Execution / Contract Tests (Pact) | Requires running live microservices or mock server daemons; slow, heavyweight, and unsuitable for lightweight pre-commit hooks. |
| Generic Linters (flake8, ruff) | Do not cross-reference mock target strings against actual project source files to verify symbol existence. |
| Pytest Plugins (`pytest-mock`) | Runtime-only; requires executing the full test suite and does not flag bare patches across un-executed test files. |

---

## 7. Acceptance Criteria for Planning

1. Detects `patch("pkg.module.non_existent_func")` when `non_existent_func` does not exist in `pkg/module.py`.
2. Flags bare `patch("pkg.module.real_func")` lacking `autospec=True` as an unconstrained mock risk.
3. Detects calls to `assert_called_with` passing invalid arguments compared to source function signature.
4. Correctly passes clean test files using `autospec=True` on valid functions.
5. Emits ANSI terminal summary, JSON report, and Markdown review card.
6. Returns exit code 1 on mock drift findings; returns exit code 0 when clean.
