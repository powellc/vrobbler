from django.urls import path
from moods import views

app_name = "moods"


urlpatterns = [
    path("mood/", views.MoodListView.as_view(), name="mood-list"),
    path(
        "mood/<slug:slug>/",
        views.MoodDetailView.as_view(),
        name="mood-detail",
    ),
]
