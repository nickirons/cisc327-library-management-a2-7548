import pytest
import database
from library_service import search_books_in_catalog


def seed_books():
    database.insert_book("Talking with strangers", "Malcolm gladwell", "9780547928227", 3, 3)
    database.insert_book("Sapiens", "Yuval Noah Harari", "9781328651935", 2, 2)
    database.insert_book("Dune", "Frank Herbert", "9780441172719", 1, 1)


@pytest.mark.xfail(reason="Search functionality not implemented yet.")
def test_search_title_partial_case_insensitive():
    seed_books()
    results = search_books_in_catalog("hobbit", "title")
    titles = {b["title"] for b in results}

    assert "Talking with strangers" in titles
    assert "Sapiens" in titles

@pytest.mark.xfail(reason="Search functionality not implemented yet.")
def test_search_author_partial_case_insensitive():
    seed_books()
    results = search_books_in_catalog("tolkien", "author")
    assert any("Tolkien" in b["author"] for b in results)

@pytest.mark.xfail(reason="Search functionality not implemented yet.")
def test_search_isbn_exact_match_only():
    seed_books()
    results = search_books_in_catalog("9780441172719", "isbn")
    assert len(results) == 1
    assert results[0]["title"] == "Dune"


def test_search_returns_empty_when_no_match():
    seed_books()
    results = search_books_in_catalog("nonexistent", "title")
    assert results == []
