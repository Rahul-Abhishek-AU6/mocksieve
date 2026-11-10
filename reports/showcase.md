# Showcase & Visual Asset Report: MockSieve

Date: 2026-11-11 (IST)  
Stage: Showcase  
Project: **MockSieve**

---

## 1. Visual Release Assets

Two distinct, complementary visual assets have been prepared and linked in `README.md` per cross-agent protocol Rule 6 and Rule 7:

1. **Truthful Behavioral Terminal Demo**:
   - **Path**: `assets/mocksieve-terminal-demo.svg`
   - **Origin**: Directly captured from the exact ANSI output produced during Step 5 of `demo.py`.
   - **Content**: Reproduces actual terminal execution flagging 1 ghost mock target (`services.billing.calculate_tax` in `tests/test_billing.py:3`) and unconstrained mock warnings, exiting with code 1.
   - **Integrity**: Zero mockups or marketing embellishments; fully reproducible by running `python3 demo.py`.

2. **Explanatory Conceptual AI Architecture Diagram**:
   - **Path**: `assets/mocksieve-architecture-concept.png`
   - **Origin**: Generated using the built-in image-generation tool per user authorization under Rule 7.
   - **Content**: Clean dark-mode diagram depicting unit test mocks on the left, the central AST validation filter, and verified code signatures with a green shield next to a shattered red phantom function on the right.
   - **Disclosure**: Explicitly labeled in `README.md` as a conceptual illustration (`Figure 1: Conceptual illustration`).

---

## 2. Documentation Review

The `README.md` includes:
- Problem framing: The "Mocks Pass, Production Fails" trap and unconstrained "infinite yes-men" mocks.
- Complete feature inventory across AST indexing, ghost target detection, and autospec auditing.
- Ready-to-use GitHub Actions workflow and pre-commit hook configurations.
- Clear boundary statements and limitations.
