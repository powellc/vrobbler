# Generated by Django 4.1.5 on 2023-01-12 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0002_episode_run_time_episode_run_time_ticks_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='episode',
            name='pub_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
