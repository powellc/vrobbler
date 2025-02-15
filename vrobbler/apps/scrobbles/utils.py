import logging
import re
from datetime import datetime, timedelta, tzinfo

import pytz
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from profiles.models import UserProfile
from profiles.utils import now_user_timezone
from scrobbles.constants import LONG_PLAY_MEDIA
from scrobbles.tasks import process_lastfm_import, process_retroarch_import

logger = logging.getLogger(__name__)
User = get_user_model()


def timestamp_user_tz_to_utc(timestamp: int, user_tz: tzinfo) -> datetime:
    return user_tz.localize(datetime.utcfromtimestamp(timestamp)).astimezone(
        pytz.utc
    )


def convert_to_seconds(run_time: str) -> int:
    """Jellyfin sends run time as 00:00:00 string. We want the run time to
    actually be in seconds so we'll convert it"

    This is actually deprecated, as we now convert to seconds before saving.
    But for older videos, we'll leave this here.
    """
    run_time_int = 0
    if ":" in str(run_time):
        run_time_list = run_time.split(":")
        hours = int(run_time_list[0])
        minutes = int(run_time_list[1])
        seconds = int(run_time_list[2])
        run_time_int = int((((hours * 60) + minutes) * 60) + seconds)
    return run_time_int


def get_scrobbles_for_media(media_obj, user: User) -> models.QuerySet:
    Scrobble = apps.get_model(app_label="scrobbles", model_name="Scrobble")

    media_query = None
    media_class = media_obj.__class__.__name__
    if media_class == "Book":
        media_query = models.Q(book=media_obj)
    if media_class == "VideoGame":
        media_query = models.Q(video_game=media_obj)

    if not media_query:
        logger.warn("Do not know about media {media_class} 🙍")
        return []
    return Scrobble.objects.filter(media_query, user=user)


def get_recently_played_board_games(user: User) -> dict:
    ...


def get_long_plays_in_progress(user: User) -> dict:
    """Find all books where the last scrobble is not marked complete"""
    media_dict = {
        "active": [],
        "inactive": [],
    }
    now = now_user_timezone(user.profile)
    for app, model in LONG_PLAY_MEDIA.items():
        media_obj = apps.get_model(app_label=app, model_name=model)
        for media in media_obj.objects.all():
            last_scrobble = media.scrobble_set.filter(user=user).last()
            if last_scrobble and last_scrobble.long_play_complete == False:
                days_past = (now - last_scrobble.timestamp).days
                if days_past > 7:
                    media_dict["inactive"].append(media)
                else:
                    media_dict["active"].append(media)
    media_dict["active"].reverse()
    media_dict["inactive"].reverse()
    return media_dict


def get_long_plays_completed(user: User) -> list:
    """Find all books where the last scrobble is not marked complete"""
    media_list = []
    for app, model in LONG_PLAY_MEDIA.items():
        media_obj = apps.get_model(app_label=app, model_name=model)
        for media in media_obj.objects.all():
            if (
                media.scrobble_set.all()
                and media.scrobble_set.filter(user=user)
                .order_by("timestamp")
                .last()
                .long_play_complete
                == True
            ):
                media_list.append(media)
    return media_list


def import_lastfm_for_all_users(restart=False):
    """Grab a list of all users with LastFM enabled and kickoff imports for them"""
    LastFmImport = apps.get_model("scrobbles", "LastFMImport")
    lastfm_enabled_user_ids = UserProfile.objects.filter(
        lastfm_username__isnull=False,
        lastfm_password__isnull=False,
        lastfm_auto_import=True,
    ).values_list("user_id", flat=True)

    lastfm_import_count = 0

    for user_id in lastfm_enabled_user_ids:
        lfm_import, created = LastFmImport.objects.get_or_create(
            user_id=user_id, processed_finished__isnull=True
        )
        if not created and not restart:
            logger.info(
                f"Not resuming failed LastFM import {lfm_import.id} for user {user_id}, use restart=True to restart"
            )
            continue
        process_lastfm_import.delay(lfm_import.id)
        lastfm_import_count += 1
    return lastfm_import_count


def import_retroarch_for_all_users(restart=False):
    """Grab a list of all users with Retroarch enabled and kickoff imports for them"""
    RetroarchImport = apps.get_model("scrobbles", "RetroarchImport")
    retroarch_enabled_user_ids = UserProfile.objects.filter(
        retroarch_path__isnull=False,
        retroarch_auto_import=True,
    ).values_list("user_id", flat=True)

    retroarch_import_count = 0

    for user_id in retroarch_enabled_user_ids:
        retroarch_import, created = RetroarchImport.objects.get_or_create(
            user_id=user_id, processed_finished__isnull=True
        )
        if not created and not restart:
            logger.info(
                f"Not resuming failed LastFM import {retroarch_import.id} for user {user_id}, use restart=True to restart"
            )
            continue
        process_retroarch_import.delay(retroarch_import.id)
        retroarch_import_count += 1
    return retroarch_import_count


def delete_zombie_scrobbles(dry_run=True):
    """Look for any scrobble over a day old that is not paused and still in progress and delete it"""
    Scrobble = apps.get_model("scrobbles", "Scrobble")
    now = timezone.now()
    three_days_ago = now - timedelta(days=3)

    # TODO This should be part of a custom manager
    zombie_scrobbles = Scrobble.objects.filter(
        timestamp__lte=three_days_ago,
        is_paused=False,
        played_to_completion=False,
    )

    zombies_found = zombie_scrobbles.count()

    if not dry_run:
        logger.info(f"Deleted {zombies_found} zombie scrobbles")
        zombie_scrobbles.delete()
        return zombies_found

    logger.info(
        f"Found {zombies_found} zombie scrobbles to delete, use dry_run=False to proceed"
    )
    return zombies_found


def media_class_to_foreign_key(media_class: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", media_class).lower()
