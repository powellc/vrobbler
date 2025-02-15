from unittest import skip

import pytest

from books.openlibrary import lookup_book_from_openlibrary


def test_lookup_modern_book():
    book = lookup_book_from_openlibrary("Matrix", "Lauren Groff")
    assert book.get("title") == "Matrix"
    assert book.get("openlibrary_id") == "OL32170218M"
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


@skip("This is rotten in OL, updated but waiting for it to update")
def test_lookup_book():
    book = lookup_book_from_openlibrary("Hark! A Vagrant")
    assert book.get("title") == "Hark! A Vagrant"
    assert book.get("openlibrary_id") == "OL8837839M"
    assert book.get("ol_author_id") == "OL152472A"
