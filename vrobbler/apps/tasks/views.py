import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from scrobbles.views import ScrobbleableDetailView, ScrobbleableListView
from tasks.models import Task

from vrobbler.apps.tasks.todoist import get_todoist_access_token

logger = logging.getLogger(__name__)


class TaskListView(ScrobbleableListView):
    model = Task


class TaskDetailView(ScrobbleableDetailView):
    model = Task


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def todoist_oauth(request):
    logger.info(
        "[todoist_oauth] called",
        extra={"user_id": request.user.id, "get_data": request.GET},
    )

    get_todoist_access_token(
        request.user.id, request.GET.get("state"), request.GET.get("code")
    )

    logger.info(
        "[todoist_oauth] finished",
        extra={"user_id": request.user.id},
    )
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Todoist successfully configured",
    )

    success_url = reverse_lazy("vrobbler-home")
    return HttpResponseRedirect(success_url)
