# Generated by Django 4.2.11 on 2024-05-07 13:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("lifeevents", "0001_initial"),
        ("scrobbles", "0055_rename_scrobble_log_scrobble_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrobble",
            name="life_event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="lifeevents.lifeevent",
            ),
        ),
        migrations.AlterField(
            model_name="scrobble",
            name="media_type",
            field=models.CharField(
                choices=[
                    ("Video", "Video"),
                    ("Track", "Track"),
                    ("PodcastEpisode", "Podcast episode"),
                    ("SportEvent", "Sport event"),
                    ("Book", "Book"),
                    ("VideoGame", "Video game"),
                    ("BoardGame", "Board game"),
                    ("GeoLocation", "GeoLocation"),
                    ("WebPage", "Web Page"),
                    ("LifeEvent", "Life event"),
                ],
                default="Video",
                max_length=14,
            ),
        ),
    ]
