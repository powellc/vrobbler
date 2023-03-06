from django.views import generic
from books.models import Book, Author


class BookListView(generic.ListView):
    model = Book
    paginate_by = 20


class BookDetailView(generic.DetailView):
    model = Book
    slug_field = "uuid"


class AuthorDetailView(generic.DetailView):
    model = Author
    slug_field = "uuid"
