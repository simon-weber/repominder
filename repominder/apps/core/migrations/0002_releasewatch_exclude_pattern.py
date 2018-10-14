# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-27 01:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_squashed_0013_auto_20171119_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='releasewatch',
            name='exclude_pattern',
            field=models.CharField(blank=True, default='[!*]', help_text='A shell pattern to match commit messages that shouldn\'t count as a release. The default matches nothing. <a href="https://docs.python.org/2/library/fnmatch.html">More details</a>.', max_length=256),
        ),
    ]