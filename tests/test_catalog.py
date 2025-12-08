import database

def test_catalog_empty_returns_no_books():
    books = database.get_all_books()
    assert books == []


def test_catalog_returns_inserted_books_sorted_by_title():
    database.insert_book("Anson Elayari", "Author Z", "9780000000001", 1, 1)
    database.insert_book("Alpha", "Author A", "9780000000002", 2, 2)

    books = database.get_all_books()
    titles = [b["title"] for b in books]

    assert titles == ["Alpha", "Anson Elayari Bio"]
    assert books[0]["available_copies"] == books[0]["total_copies"]


def test_catalog_book_fields_present():
    database.insert_book("Field Test", "Author F", "9780000000003", 1, 1)
    book = database.get_all_books()[0]

    assert set(["id", "title", "author", "isbn", "available_copies", "total_copies"]).issubset(
        book.keys()
    )



def test_catalog_reflects_availability_changes():
    database.insert_book("Avail Test", "Author A", "9780000000004", 2, 2)
    book = database.get_book_by_isbn("9780000000004")
    database.update_book_availability(book["id"], -1)

    updated = database.get_book_by_id(book["id"])
    assert updated["available_copies"] == 1
