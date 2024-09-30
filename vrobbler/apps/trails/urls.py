from django.urls import path
from trails import views

app_name = "trails"


urlpatterns = [
    path("trails/", views.TrailListView.as_view(), name="trail_list"),
    path(
        "trails/<slug:slug>/",
        views.TrailDetailView.as_view(),
        name="trail_detail",
    ),
]
