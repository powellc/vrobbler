# Generated by Django 4.2.9 on 2024-02-20 00:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("scrobbles", "0049_rename_webpage_scrobble_web_page"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ScrobbledPage",
        ),
    ]
