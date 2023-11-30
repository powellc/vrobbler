from django.urls import path
from webpages import views

app_name = "webpages"


urlpatterns = [
    path("webpage/", views.WebPageListView.as_view(), name="webpage_list"),
    path(
        "webpage/<slug:slug>/",
        views.WebPageDetailView.as_view(),
        name="webpage_detail",
    ),
]
