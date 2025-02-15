# Generated by Django 4.1.7 on 2023-05-25 02:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("scrobbles", "0040_alter_scrobble_media_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="RetroarchImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                (
                    "processing_started",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "processed_finished",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("process_log", models.TextField(blank=True, null=True)),
                ("process_count", models.IntegerField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Retroarch Import",
            },
        ),
    ]
