# Generated by Django 4.1.5 on 2023-01-05 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrobbles', '0004_scrobble_scrobble_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrobble',
            name='playback_position_ticks',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
