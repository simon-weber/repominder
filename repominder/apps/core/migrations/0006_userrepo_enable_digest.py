# Generated by Django 2.2.16 on 2020-11-25 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_auto_20201122_1718"),
    ]

    operations = [
        migrations.AddField(
            model_name="userrepo",
            name="enable_digest",
            field=models.BooleanField(default=False),
        ),
    ]
