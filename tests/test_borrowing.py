from datetime import datetime, timedelta

import database
from library_service import borrow_book_by_patron


def add_book(isbn="9781111111111", copies=2):
    database.insert_book("Borrow Me", "Author", isbn, copies, copies)
    return database.get_book_by_isbn(isbn)


def test_borrow_success_reduces_availability():
    book = add_book()

    success, message = borrow_book_by_patron("123456", book["id"])
    updated = database.get_book_by_id(book["id"])

    assert success is True
    assert "successfully borrowed" in message.lower()
    assert updated["available_copies"] == book["available_copies"] - 1


def test_borrow_rejects_invalid_patron_id():
    book = add_book("9782222222222")
    success, message = borrow_book_by_patron("12ab56", book["id"])

    assert success is False
    assert "invalid patron id" in message.lower()


def test_borrow_rejects_unavailable_book():
    database.insert_book("No Copies", "Author", "9783333333333", 1, 0)
    book = database.get_book_by_isbn("9783333333333")

    success, message = borrow_book_by_patron("123456", book["id"])

    assert success is False
    assert "not available" in message.lower()


def test_borrow_rejects_missing_book():
    success, message = borrow_book_by_patron("123456", 9999)

    assert success is False
    assert "not found" in message.lower()


def test_borrow_enforces_max_limit_of_5():
    """
    Requirement: max 5 active borrows. Current code uses '> 5', allowing a 6th book; this should fail until fixed.
    """
    target_book = add_book("9784444444444", copies=3)
    # Set 5 existing borrow records for this patron
    other_book = add_book("9785555555555", copies=5)
    for i in range(5):
        database.insert_borrow_record(
            "123456",
            other_book["id"],
            datetime.now() - timedelta(days=i),
            datetime.now() + timedelta(days=14 - i),
        )

    success, message = borrow_book_by_patron("123456", target_book["id"])

    assert success is False
    assert "maximum borrowing limit" in message.lower()
