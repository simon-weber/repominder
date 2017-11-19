# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class Repo(models.Model):
    full_name = models.CharField(max_length=256)
    users = models.ManyToManyField(User, through='UserRepo')

    def __unicode__(self):
        return "<Repo: %s>" % self.full_name

    __repr__ = __unicode__


class UserRepo(models.Model):
    repo = models.ForeignKey(Repo, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("repo", "user"),)

    def __unicode__(self):
        return "<UserRepo(%s): %s, %s>" % (self.id, self.user.username, self.repo.full_name)

    __repr__ = __unicode__


class ReleaseWatch(models.Model):
    userrepo = models.OneToOneField(UserRepo)
    dev_branch = models.CharField(
        max_length=256,
        verbose_name='development branch',
        help_text='The branch that tracks the latest code (ie, where pull requests are merged to).',
    )

    DUAL_BRANCH = 'DB'
    release_branch = models.CharField(
        max_length=256, blank=True, default='',
        help_text='The branch that tracks the most recent release.',
    )

    TAG_PATTERN = 'TP'
    tag_pattern = models.CharField(
        max_length=256, blank=True,
        default=r'*.*.*',
        help_text=(
            'A shell pattern to match release tags.'
            ' The default matches 3-part semver.'
            ' <a href="https://docs.python.org/2/library/fnmatch.html">More details</a>.'
        )
    )

    CHOICES = (
        (DUAL_BRANCH, 'dual branch'),
        (TAG_PATTERN, 'tag pattern'),
    )
    style = models.CharField(
        max_length=2,
        choices=CHOICES,
    )

    def __unicode__(self):
        return "<ReleaseWatch(%s): %s %s>" % (self.id, self.userrepo.repo.full_name, self.style)

    __repr__ = __unicode__
