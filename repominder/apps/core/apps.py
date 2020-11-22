# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "repominder.apps.core"

    def ready(self):
        from . import signals  # noqa
