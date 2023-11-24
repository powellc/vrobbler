from django.urls import path
from locations import views

app_name = "locations"


urlpatterns = [
    path(
        "locations/",
        views.GeoLocationListView.as_view(),
        name="geo_locations_list",
    ),
    path(
        "locations/<slug:slug>/",
        views.GeoLocationDetailView.as_view(),
        name="geo_location_detail",
    ),
]
