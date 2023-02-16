import logging
from celery import shared_task

from scrobbles.models import LastFmImport

logger = logging.getLogger(__name__)


@shared_task
def process_lastfm_import(import_id):
    lastfm_import = LastFmImport.objects.filter(id=import_id).first()
    if not lastfm_import:
        logger.warn(f"LastFmImport not found with id {import_id}")

    lastfm_import.process()
