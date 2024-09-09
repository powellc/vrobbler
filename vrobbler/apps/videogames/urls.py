from django.urls import path
from videogames import views

app_name = "videogames"


urlpatterns = [
    path(
        "video-games/",
        views.VideoGameListView.as_view(),
        name="videogame_list",
    ),
    path(
        "video-games/<slug:slug>/",
        views.VideoGameDetailView.as_view(),
        name="videogame_detail",
    ),
    path(
        "video-game-platforms/<slug:slug>/",
        views.VideoGamePlatformDetailView.as_view(),
        name="platform_detail",
    ),
]
