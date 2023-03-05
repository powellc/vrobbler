from django.urls import path
from videogames import views

app_name = "videogames"


urlpatterns = [
    path("game/", views.VideoGameListView.as_view(), name="videogame_list"),
    path(
        "game/<slug:slug>/",
        views.VideoGameDetailView.as_view(),
        name="videogame_detail",
    ),
]
