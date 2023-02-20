from rest_framework import permissions, viewsets

from books.api.serializers import (
    AuthorSerializer,
    BookSerializer,
)
from books.models import Author, Book


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all().order_by('-created')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('-created')
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]
