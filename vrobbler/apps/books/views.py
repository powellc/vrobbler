from django.views import generic
from books.models import Book, Author

from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class BookListView(ScrobbleableListView):
    model = Book


class BookDetailView(ScrobbleableDetailView):
    model = Book


class AuthorDetailView(generic.DetailView):
    model = Author
    slug_field = "uuid"
