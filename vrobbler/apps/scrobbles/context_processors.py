import pytz
from django.utils import timezone
from scrobbles.models import Scrobble


def now_playing(request):
    user = request.user
    now = timezone.now()
    if user.is_authenticated:
        if user.profile:
            timezone.activate(pytz.timezone(user.profile.timezone))
            now = timezone.localtime(timezone.now())
        return {
            'now_playing_list': Scrobble.objects.filter(
                in_progress=True,
                is_paused=False,
                user=user,
            )
        }
