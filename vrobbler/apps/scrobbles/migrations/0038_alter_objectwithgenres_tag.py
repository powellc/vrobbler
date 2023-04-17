# Generated by Django 4.1.7 on 2023-04-17 22:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("scrobbles", "0037_scrobble_media_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="objectwithgenres",
            name="tag",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_items",
                to="scrobbles.genre",
            ),
        ),
    ]
