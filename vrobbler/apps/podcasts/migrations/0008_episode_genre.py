# Generated by Django 4.1.5 on 2023-03-14 22:27

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ("scrobbles", "0033_genre_objectwithgenres"),
        ("podcasts", "0007_rename_run_time_episode_run_time_seconds"),
    ]

    operations = [
        migrations.AddField(
            model_name="episode",
            name="genre",
            field=taggit.managers.TaggableManager(
                help_text="A comma-separated list of tags.",
                through="scrobbles.ObjectWithGenres",
                to="scrobbles.Genre",
                verbose_name="Tags",
            ),
        ),
    ]
