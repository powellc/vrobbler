# Generated by Django 4.1.5 on 2023-02-16 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrobbles', '0018_lastfmimport'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lastfmimport',
            old_name='processed_on',
            new_name='processed_finished',
        ),
        migrations.AddField(
            model_name='lastfmimport',
            name='processing_started',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
