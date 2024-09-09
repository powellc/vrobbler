from django.urls import path
from moods import views

app_name = "moods"


urlpatterns = [
    path("moods/", views.MoodListView.as_view(), name="mood-list"),
    path(
        "moods/<slug:slug>/",
        views.MoodDetailView.as_view(),
        name="mood-detail",
    ),
]
