# Generated by Django 4.1.5 on 2023-03-15 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "videos",
            "0012_remove_series_tags_remove_video_tags_series_genre_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="next_imdb_id",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
