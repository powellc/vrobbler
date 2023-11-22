# Generated by Django 4.1.7 on 2023-11-21 23:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0001_initial"),
        ("scrobbles", "0043_scrobbledpage"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrobble",
            name="geo_location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="locations.geolocation",
            ),
        ),
        migrations.AlterField(
            model_name="scrobble",
            name="media_type",
            field=models.CharField(
                choices=[
                    ("Video", "Video"),
                    ("Track", "Track"),
                    ("Episode", "Podcast episode"),
                    ("SportEvent", "Sport event"),
                    ("Book", "Book"),
                    ("VideoGame", "Video game"),
                    ("BoardGame", "Board game"),
                    ("GeoLocation", "GeoLocation"),
                ],
                default="Video",
                max_length=14,
            ),
        ),
    ]
