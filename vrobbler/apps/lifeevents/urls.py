from django.urls import path
from lifeevents import views

app_name = "events"


urlpatterns = [
    path("events/", views.EventListView.as_view(), name="event_list"),
    path(
        "event/<slug:slug>/",
        views.EventDetailView.as_view(),
        name="event_detail",
    ),
]
