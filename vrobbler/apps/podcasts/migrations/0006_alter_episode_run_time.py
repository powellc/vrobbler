# Generated by Django 4.1.5 on 2023-03-12 01:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0005_alter_episode_options_alter_episode_title"),
    ]

    operations = [
        migrations.AlterField(
            model_name="episode",
            name="run_time",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
