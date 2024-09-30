from tasks.models import Task

from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class TaskListView(ScrobbleableListView):
    model = Task


class TaskDetailView(ScrobbleableDetailView):
    model = Task
