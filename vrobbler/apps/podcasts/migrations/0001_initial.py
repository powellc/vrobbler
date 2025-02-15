# Generated by Django 4.1.5 on 2023-01-12 17:18

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Producer',
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
                ('name', models.CharField(max_length=255)),
                (
                    'uuid',
                    models.UUIDField(
                        blank=True,
                        default=uuid.uuid4,
                        editable=False,
                        null=True,
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Podcast',
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
                ('name', models.CharField(max_length=255)),
                (
                    'uuid',
                    models.UUIDField(
                        blank=True,
                        default=uuid.uuid4,
                        editable=False,
                        null=True,
                    ),
                ),
                ('active', models.BooleanField(default=True)),
                ('url', models.URLField(blank=True, null=True)),
                (
                    'producer',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='podcasts.producer',
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Episode',
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
                ('title', models.CharField(max_length=255)),
                (
                    'uuid',
                    models.UUIDField(
                        blank=True,
                        default=uuid.uuid4,
                        editable=False,
                        null=True,
                    ),
                ),
                (
                    'mopidy_uri',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    'podcast',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='podcasts.producer',
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
