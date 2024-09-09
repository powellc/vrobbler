from django.urls import path
from boardgames import views

app_name = "boardgames"


urlpatterns = [
    path(
        "board-games/",
        views.BoardGameListView.as_view(),
        name="boardgame_list",
    ),
    path(
        "board-games/<slug:slug>/",
        views.BoardGameDetailView.as_view(),
        name="boardgame_detail",
    ),
    path(
        "board-game-publisher/<slug:slug>/",
        views.BoardGamePublisherDetailView.as_view(),
        name="publisher_detail",
    ),
]
