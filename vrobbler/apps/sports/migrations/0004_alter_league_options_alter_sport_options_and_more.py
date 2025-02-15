# Generated by Django 4.1.5 on 2023-01-22 20:20

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('sports', '0003_sport_league_sport'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='league',
            options={},
        ),
        migrations.AlterModelOptions(
            name='sport',
            options={},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={},
        ),
        migrations.RemoveField(
            model_name='sportevent',
            name='league',
        ),
        migrations.AlterField(
            model_name='league',
            name='thesportsdb_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='sport',
            name='thesportsdb_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='thesportsdb_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='Season',
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
                (
                    'thesportsdb_id',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    'league',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='sports.league',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Round',
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
                (
                    'thesportsdb_id',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    'season',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='sports.season',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Player',
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
                (
                    'thesportsdb_id',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    'league',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='sports.league',
                    ),
                ),
                (
                    'team',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='sports.team',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='sportevent',
            name='player_one',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='player_one_set',
                to='sports.player',
            ),
        ),
        migrations.AddField(
            model_name='sportevent',
            name='player_two',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='player_two_set',
                to='sports.player',
            ),
        ),
        migrations.AddField(
            model_name='sportevent',
            name='round',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to='sports.round',
            ),
        ),
        migrations.AlterField(
            model_name='sportevent',
            name='season',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to='sports.season',
            ),
        ),
    ]
