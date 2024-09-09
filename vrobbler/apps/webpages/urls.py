from django.urls import path
from webpages import views

app_name = "webpages"


urlpatterns = [
    path("webpages/", views.WebPageListView.as_view(), name="webpage-list"),
    path(
        "webpages/<slug:slug>/",
        views.WebPageDetailView.as_view(),
        name="webpage-detail",
    ),
    path(
        "webpage/<slug:slug>/read/",
        views.WebPageReadView.as_view(),
        name="webpage-read",
    ),
]
