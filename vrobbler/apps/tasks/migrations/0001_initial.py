# Generated by Django 4.2.16 on 2024-09-30 18:54

from django.db import migrations, models
import django_extensions.db.fields
import taggit.managers
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("scrobbles", "0063_scrobble_gpx_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
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
                (
                    "uuid",
                    models.UUIDField(
                        blank=True,
                        default=uuid.uuid4,
                        editable=False,
                        null=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "run_time_seconds",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "run_time_ticks",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "genre",
                    taggit.managers.TaggableManager(
                        blank=True,
                        help_text="A comma-separated list of tags.",
                        through="scrobbles.ObjectWithGenres",
                        to="scrobbles.Genre",
                        verbose_name="Tags",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
