import logging

import pendulum
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from scrobbles.scrobblers import (
    todoist_scrobble_task,
    todoist_scrobble_task_finish,
)
from profiles.models import UserProfile

logger = logging.getLogger(__name__)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def todoist_webhook(request):
    post_data = request.data
    logger.info(
        "[todoist_webhook] called",
        extra={"post_data": post_data},
    )
    todoist_type, todoist_event = post_data.get("event_name").split(":")
    event_data = post_data.get("event_data", {})
    todoist_task = {
        "todoist_id": event_data.get("id"),
        "todoist_label_list": event_data.get("labels"),
        "todoist_type": todoist_type,
        "todoist_event": todoist_event,
        "todoist_project_id": event_data.get("project_id"),
        "description": event_data.get("content"),
        "details": event_data.get("description"),
    }

    if todoist_task["todoist_type"] != "item" or todoist_task[
        "todoist_event"
    ] not in [
        "updated",
        "completed",
    ]:
        logger.info(
            "[todoist_webhook] ignoring wrong todoist type or event",
            extra={
                "todoist_type": todoist_task["todoist_type"],
                "todoist_event": todoist_task["todoist_event"],
            },
        )
        return Response({}, status=status.HTTP_304_NOT_MODIFIED)

    user_id = (
        UserProfile.objects.filter(todoist_user_id=post_data.get("user_id"))
        .first()
        .user_id
    )
    # TODO huge hack, find a way to populate user id from Todoist
    if not user_id:
        user_id = 1

    scrobble = None
    if "completed" in todoist_task["todoist_event"]:
        scrobble = todoist_scrobble_task_finish(todoist_task, user_id)
    elif "inprogress" in todoist_task["todoist_label_list"]:
        scrobble = todoist_scrobble_task(todoist_task, user_id)

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(
        "[todoist_webhook] finished",
        extra={"scrobble_id": scrobble.id},
    )
    return Response({"scrobble_id": scrobble.id}, status=status.HTTP_200_OK)
