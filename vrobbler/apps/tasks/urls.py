from django.urls import path
from tasks import views

app_name = "tasks"


urlpatterns = [
    path("tasks/", views.TaskListView.as_view(), name="task_list"),
    path(
        "tasks/<slug:slug>/",
        views.TaskDetailView.as_view(),
        name="task_detail",
    ),
]
