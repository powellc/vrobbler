import pytest

from vrobbler.apps.books.openlibrary import (
    lookup_book_from_openlibrary,
)


def test_lookup_modern_book():
    book = lookup_book_from_openlibrary("Matrix", "Lauren Groff")
    assert book.get("title") == "Matrix"
    assert book.get("openlibrary_id") == "OL47572299M"
    assert book.get("ol_author_id") == "OL3675729A"


def test_lookup_classic_book():
    book = lookup_book_from_openlibrary(
        "The Life of Castruccio Castracani", "Machiavelli"
    )
    assert book.get("title") == "The Life of Castruccio Castracani of Lucca"
    assert book.get("openlibrary_id") == "OL8950869M"
    assert book.get("ol_author_id") == "OL23135A"


def test_lookup_foreign_book():
    book = lookup_book_from_openlibrary("Ravagé", "René Barjavel")
    assert book.get("title") == "Ravage"
    assert book.get("openlibrary_id") == "OL8837839M"
    assert book.get("ol_author_id") == "OL152472A"
