# Generated by Django 4.2.11 on 2024-04-19 13:10

from datetime import datetime

import pytz
from django.conf import settings
from django.db import migrations, models


def set_default_timezone(apps, schema_editor):
    Scrobble = apps.get_model("scrobbles", "Scrobble")
    for s in Scrobble.objects.all():
        if not s.timezone:
            s.timezone = settings.TIME_ZONE

            if s.user and s.user.profile:
                s.timezone = s.user.profile.timezone

            # A shim to adjust for our change to European time for 3 months
            if (
                datetime(2023, 10, 15).replace(
                    tzinfo=pytz.timezone("Europe/Paris")
                )
                <= s.timestamp
                <= datetime(2023, 12, 15).replace(
                    tzinfo=pytz.timezone("Europe/Paris")
                )
            ):
                s.timezone = "Europe/Paris"
            s.save(update_fields=["timezone"])


class Migration(migrations.Migration):

    dependencies = [
        ("scrobbles", "0050_delete_scrobbledpage"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrobble",
            name="timezone",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.RunPython(set_default_timezone),
    ]
