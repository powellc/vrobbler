from django.urls import path
from trails import views

app_name = "trials"


urlpatterns = [
    path("trails/", views.TrailListView.as_view(), name="trail-list"),
    path(
        "trails/<slug:slug>/",
        views.TrailDetailView.as_view(),
        name="trail-detail",
    ),
]
