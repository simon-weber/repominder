# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Repo, UserRepo, ReleaseWatch

admin.site.register(Repo)
admin.site.register(UserRepo)
admin.site.register(ReleaseWatch)
