from django.urls import path
from lifeevents import views

app_name = "lifeevents"


urlpatterns = [
    path(
        "lifeevents/", views.LifeEventListView.as_view(), name="lifeevent_list"
    ),
    path(
        "lifeevent/<slug:slug>/",
        views.LifeEventDetailView.as_view(),
        name="life-event_detail",
    ),
]
