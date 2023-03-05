# Generated by Django 4.1.5 on 2023-03-05 01:04

from django.db import migrations, models
import encrypted_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0003_userprofile_twitch_client_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="twitch_token",
            field=encrypted_field.fields.EncryptedField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="twitch_token_expires",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
