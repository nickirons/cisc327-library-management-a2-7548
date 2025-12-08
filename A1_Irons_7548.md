# Assignment 1 - Nicholas Irons - ID: 20427548 - I didn't think there were groups?

# Implementation Status (per requirements_specification.md)
| Function/Requirement | Status (complete/partial) | What’s missing or issues |
| --- | --- | --- |
| 1 Add Book | Partial | Does not enforce ISBN digits, only length 13. |
| 2 Catalog Display | Complete | |
| 3 Borrowing | Partial | Borrow limit check uses > 5, so patrons can take a 6th book, it should be `>= 5`. |
| 4 Return | Not implemented | No verification, availability update, or late-fee handling. |
| 5 Late Fee API | Not implemented | API returns 501/not implemented. |
| 6 Search | Not implemented | Just returns and empty list |
| 7 Patron Status | Not implemented | No menu option or UI for patron status |

# Tests Summary
- tests/test_add_book.py: 1. validation (valid add, missing title, duplicate ISBN, invalid length, non-digit ISBN requirement).
- tests/test_catalog.py: 2. catalog data (empty state, ordering, field presence, availability changes).
- tests/test_borrowing.py: 3. borrow flow (success path, invalid patron, unavailable/missing book, max-5 limit bug).
- tests/test_return.py: 4 expected return behavior (fail function not implemented).
- tests/test_late_fee_api.py: 5. late fee calculation cases (fail, not implemented).
- tests/test_search.py: 6. search by title/author/ISBN and no-match case (positive cases fail, not implemented).
- tests/test_patron_status.py; 7. patron status report scenarios (fail, not implemented).
