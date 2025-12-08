# AI-Assisted Test Generation (Task 3)

- **AI tool used:** ChatGPT (OpenAI)
- **Initial prompt:**
  ```
  Generate pytest test cases for the library_service functions (R1–R7) of a Flask/SQLite
  library system. Functions include add_book_to_catalog, borrow_book_by_patron,
  return_book_by_patron, calculate_late_fee_for_book, search_books_in_catalog,
  get_patron_status_report. Follow these requirements: title max 200, author max 100,
  ISBN exactly 13 digits, patron ID 6 digits, max 5 active borrows, 14-day loan, late fee
  $0.50/day first 7 overdue, then $1/day, max $15, search title/author partial
  case-insensitive, ISBN exact. Use temp DB fixture if needed.
  ```
- **Follow-up prompts:**
  - “Add negative tests for invalid patron IDs and invalid search types.”
  - “Include an overdue return case that should surface a late fee.”

## AI-Generated Test Cases (do not run by default; for report inclusion)

```python
from datetime import datetime, timedelta
import pytest
import database
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
    get_patron_status_report,
)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "ai_test.db"
    monkeypatch.setattr(database, "DATABASE", str(db_path))
    database.init_database()
    yield


def test_add_book_valid_and_duplicate_isbn():
    ok, msg = add_book_to_catalog("AI Book", "Bot Author", "1234567890123", 2)
    assert ok is True and "successfully" in msg.lower()
    ok2, msg2 = add_book_to_catalog("AI Book 2", "Bot Author", "1234567890123", 1)
    assert ok2 is False and "exists" in msg2.lower()


def test_add_book_rejects_bad_inputs():
    assert add_book_to_catalog("", "Auth", "1234567890123", 1)[0] is False
    assert add_book_to_catalog("T", "", "1234567890123", 1)[0] is False
    assert add_book_to_catalog("T", "A", "123", 1)[0] is False  # bad ISBN length
    assert add_book_to_catalog("T", "A", "12345678901ab", 1)[0] is False  # non-digit ISBN


def test_borrow_enforces_limits_and_ids():
    database.insert_book("Borrowable", "Auth", "9780000000001", 1, 1)
    book = database.get_book_by_isbn("9780000000001")
    ok, _ = borrow_book_by_patron("123456", book["id"])
    assert ok is True
    ok2, msg2 = borrow_book_by_patron("12ab56", book["id"])
    assert ok2 is False and "invalid patron id" in msg2.lower()


def test_borrow_max_five_active():
    database.insert_book("Limit Book", "Auth", "9780000000002", 5, 5)
    b = database.get_book_by_isbn("9780000000002")
    # seed 5 borrows
    for _ in range(5):
        database.insert_borrow_record("999999", b["id"], datetime.now(), datetime.now() + timedelta(days=14))
    ok, msg = borrow_book_by_patron("999999", b["id"])
    assert ok is False and "maximum borrowing limit" in msg.lower()


def test_return_overdue_updates_availability_and_fee():
    database.insert_book("Returnable", "Auth", "9780000000003", 1, 0)
    book = database.get_book_by_isbn("9780000000003")
    past = datetime.now() - timedelta(days=25)
    database.insert_borrow_record("123456", book["id"], past, past + timedelta(days=14))
    ok, msg = return_book_by_patron("123456", book["id"])
    assert ok is True and "late fee" in msg.lower()
    updated = database.get_book_by_id(book["id"])
    assert updated["available_copies"] == 1


def test_late_fee_calculation_ranges_and_caps():
    database.insert_book("Fee Book", "Auth", "9780000000004", 1, 0)
    b = database.get_book_by_isbn("9780000000004")
    borrow_date = datetime.now() - timedelta(days=40)  # 26 days overdue
    database.insert_borrow_record("123456", b["id"], borrow_date, borrow_date + timedelta(days=14))
    result = calculate_late_fee_for_book("123456", b["id"])
    assert result["days_overdue"] == 26
    assert result["fee_amount"] == 15.00  # capped


def test_search_title_author_isbn_and_invalid_type():
    database.insert_book("The Hobbit", "Tolkien", "9780547928227", 1, 1)
    database.insert_book("Hobbit Companion", "Corey Olsen", "9781328651935", 1, 1)
    by_title = search_books_in_catalog("hobbit", "title")
    assert len(by_title) == 2
    by_author = search_books_in_catalog("tolkien", "author")
    assert any("tolkien" in b["author"].lower() for b in by_author)
    by_isbn = search_books_in_catalog("9781328651935", "isbn")
    assert len(by_isbn) == 1 and by_isbn[0]["title"] == "Hobbit Companion"
    assert search_books_in_catalog("x", "badtype") == []


def test_patron_status_reports_current_borrows_and_fees():
    database.insert_book("Status Book", "Auth", "9780000000005", 1, 0)
    b = database.get_book_by_isbn("9780000000005")
    borrow_date = datetime.now() - timedelta(days=20)
    database.insert_borrow_record("123456", b["id"], borrow_date, borrow_date + timedelta(days=14))
    report = get_patron_status_report("123456")
    assert report["books_borrowed_count"] == 1
    assert report["total_late_fees"] > 0
    assert report["currently_borrowed"][0]["book_id"] == b["id"]


def test_patron_status_invalid_id():
    report = get_patron_status_report("abc123")
    assert report["status"].lower().startswith("invalid patron id")
```
