from datetime import datetime, timedelta
import database
from services.library_service import calculate_late_fee_for_book


def seed_borrow(patron_id: str, book_id: int, borrow_days_ago: int):
    borrow_date = datetime.now() - timedelta(days=borrow_days_ago)
    due_date = borrow_date + timedelta(days=14)
    database.insert_borrow_record(patron_id, book_id, borrow_date, due_date)


def test_late_fee_overdue_book():
    database.insert_book("Overdue", "Author", "9788888888888", 1, 0)
    book = database.get_book_by_isbn("9788888888888")
    seed_borrow("123456", book["id"], borrow_days_ago=25)  # 11 days overdue

    result = calculate_late_fee_for_book("123456", book["id"])

    assert result["days_overdue"] == 11
    assert abs(result["fee_amount"] - 7.5) < 0.01  #7 days * 0.50 + 4 days


def test_late_fee_not_overdue():
    database.insert_book("On Time", "Author", "9789999999999", 1, 0)
    book = database.get_book_by_isbn("9789999999999")
    seed_borrow("123456", book["id"], borrow_days_ago=5)  # Not overdur
    result = calculate_late_fee_for_book("123456", book["id"])

    assert result["days_overdue"] == 0
    assert result["fee_amount"] == 0
