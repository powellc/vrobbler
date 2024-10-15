import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    # Disregard progress updates
    if in_progress and is_music:
        logger.info(
            "[jellyfin_webhook] ignoring update of music in progress",
            extra={"post_data": post_data},
        )
        return Response({}, status=status.HTTP_304_NOT_MODIFIED)

    scrobble = todoist_scrobble_task(post_data, request.user.id)

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(
        "[jellyfin_webhook] finished",
        extra={"scrobble_id": scrobble.id},
    )
    return Response({"scrobble_id": scrobble.id}, status=status.HTTP_200_OK)
