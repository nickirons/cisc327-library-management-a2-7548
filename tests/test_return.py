from datetime import datetime, timedelta
import database
from library_service import return_book_by_patron


def test_return_success_updates_availability_and_includes_late_fee():
    database.insert_book("Returnable", "Author", "9786666666666", 1, 0)
    book = database.get_book_by_isbn("9786666666666")
    database.insert_borrow_record(
        "123456",
        book["id"],
        datetime.now() - timedelta(days=20),
        datetime.now() - timedelta(days=6),
    )

    success, message = return_book_by_patron("123456", book["id"])
    updated = database.get_book_by_id(book["id"])

    assert success is True
    assert "late fee" in message.lower()
    assert updated["available_copies"] == 1


def test_return_rejects_if_not_borrowed_by_patron():
    database.insert_book("ReturnCheck", "Author", "9787777777777", 1, 0)
    book = database.get_book_by_isbn("9787777777777")
    # Borrowed by someone else
    database.insert_borrow_record(
        "999999",
        book["id"],
        datetime.now() - timedelta(days=5),
        datetime.now() + timedelta(days=9),
    )

    success, message = return_book_by_patron("123456", book["id"])

    assert success is False
    assert "was not borrowed by this patron" in message.lower()
