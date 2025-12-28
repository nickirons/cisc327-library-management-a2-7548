import database
from services.library_service import search_books_in_catalog


def seed_books():
    database.insert_book("Talking with strangers", "Malcolm Gladwell", "9781549150340", 3, 3)
    database.insert_book("Sapiens", "Yuval Noah Harari", "9780062316110", 2, 2)

def test_search_title_partial_case_insensitive():
    seed_books()
    results = search_books_in_catalog("s", "title")
    titles = {b["title"] for b in results}

    assert "Talking with strangers" in titles
    assert "Sapiens" in titles

def test_search_author_partial_case_insensitive():
    seed_books()
    results = search_books_in_catalog("gladwell", "author")
    assert any("gladwell" in b["author"].lower() for b in results)

def test_search_isbn_exact_match_only():
    seed_books()
    results = search_books_in_catalog("9780062316110", "isbn")
    assert len(results) == 1
    assert results[0]["title"] == "Sapiens"

def test_search_returns_empty_when_no_match():
    seed_books()
    results = search_books_in_catalog("nonexistent", "title")
    assert results == []
