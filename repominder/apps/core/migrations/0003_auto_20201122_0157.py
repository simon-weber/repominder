# Generated by Django 2.2.16 on 2020-11-22 01:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_releasewatch_exclude_pattern"),
    ]

    operations = [
        migrations.CreateModel(
            name="Installation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("installation_id", models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name="RepoInstall",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "installation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.Installation",
                    ),
                ),
                (
                    "repo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.Repo"
                    ),
                ),
            ],
            options={
                "unique_together": {("repo", "installation")},
            },
        ),
        migrations.AddField(
            model_name="repo",
            name="installations",
            field=models.ManyToManyField(
                through="core.RepoInstall", to="core.Installation"
            ),
        ),
    ]
