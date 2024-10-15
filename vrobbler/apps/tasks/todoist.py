import logging

import secrets

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from profiles.models import UserProfile

from vrobbler.settings import TODOIST_CLIENT_ID

logger = logging.getLogger(__name__)
User = get_user_model()

TODOIST_OAUTH_START_URL = "https://todoist.com/oauth/authorize?client_id={id}&scope=data:read_write&state=".format(
    id=TODOIST_CLIENT_ID
)
TODOIST_OAUTH_TOKEN_URL = "https://todoist.com/oauth/access_token"


def generate_todoist_oauth_url(user_id: int) -> str:
    user_profile = User.objects.filter(id=user_id).first().profile
    user_profile.todoist_state = secrets.token_hex(16)
    user_profile.save(update_fields=["todoist_state"])
    return TODOIST_OAUTH_START_URL + user_profile.todoist_state


def get_todoist_access_token(user_id: int, state: str, code: str):
    logger.info(
        "[get_todoist_access_token] called",
        extra={"state": state, "code": code},
    )
    user_profile = UserProfile.objects.filter(user_id=user_id).first()

    if not user_profile:
        raise Exception

    if user_profile.todoist_state != state:
        logger.info(
            "[get_todoist_access_token] state mismatch",
            extra={"user_id": user_id, "state": state},
        )
        raise Exception

    post_data = {
        "client_id": settings.TODOIST_CLIENT_ID,
        "client_secret": settings.TODOIST_CLIENT_SECRET,
        "code": code,
    }

    response = requests.post(TODOIST_OAUTH_TOKEN_URL, data=post_data)

    if response.status_code == 200:
        user_profile.todoist_auth_key = response.json().get("access_token")
        user_profile.todoist_state = None
        user_profile.save()

    logger.info(
        "[get_todoist_access_token] finished",
        extra={"user_id": user_profile.user.id},
    )
