from django.urls import path
from books import views

app_name = "books"


urlpatterns = [
    path("books/", views.BookListView.as_view(), name="book_list"),
    path(
        "books/<slug:slug>/",
        views.BookDetailView.as_view(),
        name="book_detail",
    ),
    path(
        "authors/<slug:slug>/",
        views.AuthorDetailView.as_view(),
        name="author_detail",
    ),
]
