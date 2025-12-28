from datetime import datetime, timedelta
import database
from services.library_service import get_patron_status_report


def test_patron_status_includes_current_borrows_and_fees():
    database.insert_book("Status Book", "Author", "9781231231231", 2, 2)
    book = database.get_book_by_isbn("9781231231231")
    database.insert_borrow_record(
        "123456",
        book["id"],
        datetime.now() - timedelta(days=20),
        datetime.now() - timedelta(days=6),  #Overdue by 6 days
    )

    report = get_patron_status_report("123456")

    assert "currently_borrowed" in report
    assert len(report["currently_borrowed"]) == 1
    assert report["total_late_fees"] > 0
    assert report["books_borrowed_count"] == 1


def test_patron_status_for_patron_with_no_records():
    report = get_patron_status_report("000000")
    assert report["currently_borrowed"] == []
    assert report["total_late_fees"] == 0
