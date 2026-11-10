# Community Launch Announcement: MockSieve

Status: **Ready for Submission**  
Project: **MockSieve**  
Public Repository: https://github.com/Rahul-Abhishek-AU6/mocksieve

---

## 1. Candidate Subreddits & Rules Review

| Subreddit | Recommended Flair | Rules & Self-Promotion Guidelines |
|---|---|---|
| **r/Python** (Primary) | `Showcase` / `Project` | Requires open-source code link, MIT license, and direct explanation. No direct commercial ads or affiliate links. |
| **r/programming** | `Discussion` | 9:1 participation ratio rule; frame as an architectural discussion around mock drift and static analysis in AI agent loops. |
| **r/devops** | `Tools` | Focus on CI/CD pipeline reliability, preventing false green tests, and pre-commit automation. |
| **r/ClaudeAI** / **r/Cursor** | `Discussion` | Highlight the specific failure mode where coding agents refactor code but leave stale mocks that falsely pass tests. |

---

## 2. Prepared Post

### Title Options
- **Option 1 (Recommended)**: *I built MockSieve: a zero-dependency CLI that catches mock drift and ghost test doubles before CI gives you false confidence*
- **Option 2**: *The "Mocks Pass, Production Fails" Trap: Why bare patches are infinite yes-men, and how to audit them in 30ms*

---

### Body

```markdown
Hey r/Python,

If you maintain unit tests or use AI coding agents (Claude Code, Cursor, Copilot, Antigravity), you’ve probably hit this frustrating trap:

1. A developer or agent refactors a service function (e.g. renaming `calculate_tax` to `calculate_invoice_tax` or adding a required argument).
2. The implementation is updated, but tests still contain `@patch("services.billing.calculate_tax")`.
3. Because standard `unittest.mock` objects are unconstrained "infinite yes-men" by default, the mock silently intercepts the call and invents a fake attribute on the fly.
4. Your test suite runs, reports **100% green**, and CI approves the PR.
5. In production, real traffic hits the real service and immediately crashes with `AttributeError` or `TypeError`!

To eliminate this gap, I built **MockSieve**: a fast, zero-dependency pre-commit and CI verification check.

### What it does:
- **Zero External Dependencies**: Built with 100% Python standard library (`ast`, `pathlib`, `json`, `argparse`). Zero pip packages needed.
- **Ghost Target Detection**: Statically cross-references `@patch("path.to.target")` and `patch.object(...)` against your actual source code AST. If the function or method was deleted or renamed, MockSieve flags it immediately.
- **Unconstrained Mock Warnings**: Identifies `@patch` calls missing `autospec=True`, warning you before bare mocks allow typos and invalid signatures to pass silently.
- **Sub-30ms Diff Mode (`--diff`)**: Audits only uncommitted changes, making it ideal as a zero-latency git pre-commit hook.
- **PR Review Cards**: Emits colored terminal receipts, structured JSON reports, and GitHub PR Markdown cards.

### Quick Start (No installation needed):
```bash
# Clone the repository
git clone https://github.com/Rahul-Abhishek-AU6/mocksieve.git
cd mocksieve

# Run interactive demo simulating a refactor mock drift
python3 demo.py

# Audit your current test suite or uncommitted changes
python3 run_mocksieve.py --diff
```

### GitHub Actions Integration:
```yaml
- name: Audit Mock Drift
  run: python3 run_mocksieve.py --strict
```

- **GitHub Repository**: https://github.com/Rahul-Abhishek-AU6/mocksieve (MIT Licensed)
- **Visuals & Architecture**: Full conceptual architectural diagram and terminal demo are in the repo README.

Would love to hear how other teams keep unit test mocks synchronized with evolving codebases!
```

---

## 3. Submission Protocol

- Target Community: `r/Python` (Showcase)
- Visual asset embedded in README: `assets/mocksieve-architecture-concept.png` & `assets/mocksieve-terminal-demo.svg`
- Verification: Live repository verified at `https://github.com/Rahul-Abhishek-AU6/mocksieve`.
