from django.urls import path
from beers import views

app_name = "beers"


urlpatterns = [
    path("beers/", views.BeerListView.as_view(), name="beer_list"),
    path(
        "beers/<slug:slug>/",
        views.BeerDetailView.as_view(),
        name="beer_detail",
    ),
]
