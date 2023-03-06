from django.urls import path
from videogames import views

app_name = "videogames"


urlpatterns = [
    path(
        "video-game/", views.VideoGameListView.as_view(), name="videogame_list"
    ),
    path(
        "video-game/<slug:slug>/",
        views.VideoGameDetailView.as_view(),
        name="videogame_detail",
    ),
    path(
        "video-game-platform/<slug:slug>/",
        views.VideoGamePlatformDetailView.as_view(),
        name="platform_detail",
    ),
]
