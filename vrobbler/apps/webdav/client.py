from webdav3.client import Client

from profiles.models import UserProfile

def get_webdav_client(user_id):
    client = None
    profile = UserProfile.objects.filter(user_id=user_id).first()

    if not profile:
        logger.info("[get_webdav_client] no profile for user", extra={"user_id": user_id})
        return

    if not profile.webdav_user:
        logger.info("[get_webdav_client] no webdave user for profile", extra={"user_id": user_id})
        return

    return Client(
        {
            'webdav_hostname': profile.webdav_url,
            'webdav_login':    profile.webdav_user,
            'webdav_password': profile.webdav_pass,
        }
    )
