from django.urls import path
from podcasts import views

app_name = "podcasts"


urlpatterns = [
    path("podcasts/", views.PodcastListView.as_view(), name="podcast_list"),
    path(
        "podcasts/<slug:slug>/",
        views.PodcastDetailView.as_view(),
        name="podcast_detail",
    ),
]
