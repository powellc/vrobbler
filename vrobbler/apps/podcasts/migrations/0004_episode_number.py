# Generated by Django 4.1.5 on 2023-01-12 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0003_episode_pub_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='episode',
            name='number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
