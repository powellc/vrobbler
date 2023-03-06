from django.urls import path
from books import views

app_name = "books"


urlpatterns = [
    path("book/", views.BookListView.as_view(), name="book_list"),
    path(
        "book/<slug:slug>/",
        views.BookDetailView.as_view(),
        name="book_detail",
    ),
    path(
        "author/<slug:slug>/",
        views.AuthorDetailView.as_view(),
        name="author_detail",
    ),
]
