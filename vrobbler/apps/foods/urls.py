from django.urls import path
from foods import views

app_name = "foods"


urlpatterns = [
    path("foods/", views.FoodListView.as_view(), name="food_list"),
    path(
        "foods/<slug:slug>/",
        views.FoodDetailView.as_view(),
        name="food_detail",
    ),
]
