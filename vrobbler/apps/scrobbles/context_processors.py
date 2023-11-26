import pytz
from django.utils import timezone

from scrobbles.constants import EXCLUDE_FROM_NOW_PLAYING
from scrobbles.models import Scrobble

def now_playing(request):
    user = request.user
    now = timezone.now()
    if not user.is_authenticated:
        return {}
    return {
        "now_playing_list": Scrobble.objects.filter(
            in_progress=True,
            is_paused=False,
            user=user,
        ).exclude(
            media_type__in=EXCLUDE_FROM_NOW_PLAYING,
        )
    }
