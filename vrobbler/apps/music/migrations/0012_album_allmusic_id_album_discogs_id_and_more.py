# Generated by Django 4.1.5 on 2023-03-02 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0011_artist_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='allmusic_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='discogs_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='rateyourmusic_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_genre',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_id',
            field=models.CharField(
                blank=True, max_length=255, null=True, unique=True
            ),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_mood',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_score',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_score_votes',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_speed',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_style',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='theaudiodb_theme',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='wikidata_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='wikipedia_slug',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
