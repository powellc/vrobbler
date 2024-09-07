from django.urls import path
from bricksets import views

app_name = "bricksets"


urlpatterns = [
    path("bricksets/", views.BrickSetListView.as_view(), name="brickset_list"),
    path(
        "bricksets/<slug:slug>/",
        views.BrickSetDetailView.as_view(),
        name="brickset_detail",
    ),
]
