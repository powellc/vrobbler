# Generated by Django 4.1.5 on 2023-03-05 19:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("videogames", "0004_alter_videogame_alternative_name_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="videogame",
            old_name="platform",
            new_name="platforms",
        ),
    ]
