import logging

import pendulum
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from scrobbles.scrobblers import (
    todoist_scrobble_task,
    todoist_scrobble_update_task,
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
    todoist_task = {}
    todoist_note = {}
    todoist_type, todoist_event = post_data.get("event_name").split(":")
    event_data = post_data.get("event_data", {})
    is_item_type = todoist_type == "item"
    is_note_type = todoist_type == "note"
    new_labels = event_data.get("labels", [])
    old_labels = (
        post_data.get("event_data_extra", {})
        .get("old_item", {})
        .get("labels", [])
    )
    # TODO Don't hard code status strings in here
    is_updated = todoist_event in ["updated"]
    is_added = todoist_event in ["added"]

    task_started = (
        "inprogress" in new_labels and "inprogress" not in old_labels
    )
    task_stopped = (
        "inprogress" not in new_labels and "inprogress" in old_labels
    )

    if is_item_type and is_updated and (task_started or task_stopped):
        todoist_task = {
            "todoist_id": event_data.get("id"),
            "todoist_label_list": event_data.get("labels"),
            "todoist_type": todoist_type,
            "todoist_event": todoist_event,
            "updated_at": event_data.get("updated_at"),
            "todoist_project_id": event_data.get("project_id"),
            "description": event_data.get("content"),
            "details": event_data.get("description"),
        }
    if is_note_type and is_added:
        task_data = event_data.get("item", {})
        todoist_note = {
            "task_id": event_data.get("item_id"),
            "todoist_id": event_data.get("id"),
            "todoist_label_list": task_data.get("labels"),
            "todoist_type": todoist_type,
            "todoist_event": todoist_event,
            "updated_at": task_data.get("updated_at"),
            "details": task_data.get("description"),
            "notes": event_data.get("content"),
            "is_deleted": True
            if event_data.get("is_deleted") == "true"
            else False,
        }

    if (is_added and not todoist_note) or (is_updated and not todoist_task):
        logger.info(
            "[todoist_webhook] ignoring wrong todoist type, event or labels",
            extra={
                "todoist_type": todoist_type,
                "todoist_event": todoist_event,
                "task_started": task_started,
                "task_stopped": task_stopped,
                "new_labels": new_labels,
                "old_labels": old_labels,
            },
        )
        return Response({}, status=status.HTTP_304_NOT_MODIFIED)

    user_id = (
        UserProfile.objects.filter(todoist_user_id=post_data.get("user_id"))
        .first()
        .user_id
    )

    scrobble = None
    if todoist_task:
        scrobble = todoist_scrobble_task(
            todoist_task, user_id, stopped=task_stopped
        )

    if todoist_note:
        scrobble = todoist_scrobble_update_task(todoist_note, user_id)

    if not scrobble:
        logger.info(
            "[todoist_webhook] finished with no note or task found",
            extra={"scrobble_id": None},
        )
        return Response(
            {"error": "No scrobble found to be updated"},
            status=status.HTTP_304_NOT_MODIFIED,
        )

    logger.info(
        "[todoist_webhook] finished",
        extra={"scrobble_id": scrobble.id},
    )
    return Response({"scrobble_id": scrobble.id}, status=status.HTTP_200_OK)
