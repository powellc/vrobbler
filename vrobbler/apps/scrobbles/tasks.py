import logging
from celery import shared_task

from scrobbles.models import AudioScrobblerTSVImport, LastFmImport

logger = logging.getLogger(__name__)


@shared_task
def process_lastfm_import(import_id):
    lastfm_import = LastFmImport.objects.filter(id=import_id).first()
    if not lastfm_import:
        logger.warn(f"LastFmImport not found with id {import_id}")

    lastfm_import.process()


@shared_task
def process_tsv_import(import_id):
    tsv_import = AudioScrobblerTSVImport.objects.filter(id=import_id).first()
    if not tsv_import:
        logger.warn(f"AudioScrobblerTSVImport not found with id {import_id}")

    tsv_import.process()
