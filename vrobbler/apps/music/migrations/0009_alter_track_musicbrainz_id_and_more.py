# Generated by Django 4.1.5 on 2023-01-19 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0008_alter_track_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='track',
            name='musicbrainz_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='track',
            unique_together={('album', 'musicbrainz_id')},
        ),
    ]
