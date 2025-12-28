import pytest

import database
from services.library_service import add_book_to_catalog


def test_add_book_success():
    success, message = add_book_to_catalog("Test Book", "Author", "1234567890123", 3)
    saved = database.get_book_by_isbn("1234567890123")

    assert success is True
    assert "successfully added" in message.lower()
    assert saved["title"] == "Test Book"
    assert saved["available_copies"] == 3
    assert saved["total_copies"] == 3


def test_add_book_missing_title():
    success, message = add_book_to_catalog("", "Author", "1234567890123", 2)

    assert success is False
    assert "title is required" in message.lower()


def test_add_book_duplicate_isbn():
    add_book_to_catalog("First", "Author", "1234567890123", 1)
    success, message = add_book_to_catalog("Second", "Author 2", "1234567890123", 1)

    assert success is False
    assert "already exists" in message.lower()


def test_add_book_invalid_isbn_length():
    success, message = add_book_to_catalog("Short ISBN", "Author", "123", 1)

    assert success is False
    assert "exactly 13 digits" in message.lower()


def test_add_book_isbn_must_be_digits():
    # ISBN must be exactly 13 digits (not just length 13). 
    # The current stuff only checks length so this test should expose the bug.
    success, message = add_book_to_catalog("Non-digit ISBN", "Author", "12345678901ab", 1)

    assert success is False
    assert "13 digits" in message
