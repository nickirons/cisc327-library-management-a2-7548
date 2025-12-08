# Test-Case Comparison & Analysis (Task 4)

- **Human-written tests (tests/ + sample_test.py):**
  - Strong alignment to requirements R1–R7; each function has positive/negative cases.
  - Uses a shared temp DB fixture (root `conftest.py`) for isolation.
  - Edge cases: duplicate ISBN, non-digit ISBN, max-5 borrow limit, unavailable/missing book, search variants, overdue fee calculation at specific days, return path validation.
  - UI/report note: Patron status logic is tested; UI/menu link is still flagged separately.

- **AI-generated tests (ai_generated_tests.md):**
  - Similar breadth (R1–R7) but different data/angles: 26-day overdue to hit $15 cap, invalid search type, invalid patron status ID check.
  - Includes its own temp DB fixture inside the snippet; not wired into the runnable suite.
  - Some assertions are looser (e.g., message substring checks) and less specific about ordering/fields.

- **Quality/coverage comparison:**
  - Overlap: Both sets cover happy paths and key negatives for add/borrow/return/late fee/search/status.
  - Gaps in AI set: Does not check catalog ordering/field presence; fewer message/format checks; relies on its own fixture instead of project standard.
  - Extras in AI set: Invalid search type; explicit $15 cap case; invalid patron status ID.
  - Human set has stronger structure (shared fixtures, deterministic data) and tighter requirement assertions.

- **Conclusion:** Human-written tests are more aligned to project standards and requirement-specific checks; AI-generated tests add a few useful negatives (invalid search type, invalid patron ID, fee cap) that could be merged after review. For CI, keep the human suite as the source of truth and treat AI cases as optional candidates to incorporate selectively.
