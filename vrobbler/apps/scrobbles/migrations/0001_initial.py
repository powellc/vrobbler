# Generated by Django 4.1.5 on 2023-01-04 21:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('videos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Scrobble',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'created',
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name='modified'
                    ),
                ),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                (
                    'playback_position_ticks',
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    'playback_position',
                    models.CharField(blank=True, max_length=8, null=True),
                ),
                ('is_paused', models.BooleanField(default=False)),
                ('played_to_completion', models.BooleanField(default=False)),
                (
                    'source',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ('source_id', models.TextField(blank=True, null=True)),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'video',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='videos.video',
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
