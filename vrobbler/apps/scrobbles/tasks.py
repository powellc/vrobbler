import logging

from celery import shared_task
from django.apps import apps
from django.contrib.auth import get_user_model
from scrobbles.stats import build_yesterdays_charts_for_user

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def process_retroarch_import(import_id):
    RetroarchImport = apps.get_model("scrobbles", "RetroarchImport")
    retroarch_import = RetroarchImport.objects.filter(id=import_id).first()
    if not retroarch_import:
        logger.warn(f"RetroarchImport not found with id {import_id}")

    retroarch_import.process()


@shared_task
def process_lastfm_import(import_id):
    LastFmImport = apps.get_model("scrobbles", "LastFMImport")
    lastfm_import = LastFmImport.objects.filter(id=import_id).first()
    if not lastfm_import:
        logger.warn(f"LastFmImport not found with id {import_id}")

    lastfm_import.process()


@shared_task
def process_tsv_import(import_id):
    AudioScrobblerTSVImport = apps.get_model(
        "scrobbles", "AudioscrobblerTSVImport"
    )
    tsv_import = AudioScrobblerTSVImport.objects.filter(id=import_id).first()
    if not tsv_import:
        logger.warn(f"AudioScrobblerTSVImport not found with id {import_id}")

    tsv_import.process()


@shared_task
def process_koreader_import(import_id):
    KoReaderImport = apps.get_model("scrobbles", "KoReaderImport")
    koreader_import = KoReaderImport.objects.filter(id=import_id).first()
    if not koreader_import:
        logger.warn(f"KOReaderImport not found with id {import_id}")

    koreader_import.process()


@shared_task
def create_yesterdays_charts():
    for user in User.objects.all():
        build_yesterdays_charts_for_user(user)
