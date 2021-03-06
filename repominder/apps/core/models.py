# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    last_userrepo_refresh = models.DateTimeField(default=timezone.now)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return "<Profile: %s>" % self.user

    __repr__ = __str__


class Installation(models.Model):
    installation_id = models.PositiveIntegerField(db_index=True)
    users = models.ManyToManyField(User, through="UserInstall")

    def __str__(self):
        return "<Installation: %s>" % self.installation_id

    __repr__ = __str__


class Repo(models.Model):
    full_name = models.CharField(max_length=256, db_index=True)
    users = models.ManyToManyField(User, through="UserRepo")
    installations = models.ManyToManyField(Installation, through="RepoInstall")

    def __str__(self):
        return "<Repo: %s>" % self.full_name

    __repr__ = __str__


class UserInstall(models.Model):
    installation = models.ForeignKey(Installation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("installation", "user"),)

    def __str__(self):
        return "<UserInstall(%s): %s, %s>" % (
            self.id,
            self.user.username,
            self.installation.installation_id,
        )

    __repr__ = __str__


class RepoInstall(models.Model):
    repo = models.ForeignKey(Repo, on_delete=models.CASCADE)
    installation = models.ForeignKey(Installation, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("repo", "installation"),)

    def __str__(self):
        return "<RepoInstall(%s): %s, %s>" % (
            self.id,
            self.repo.full_name,
            self.installation.installation_id,
        )

    __repr__ = __str__


class UserRepo(models.Model):
    repo = models.ForeignKey(Repo, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enable_digest = models.BooleanField(
        default=False,
        help_text="Enable to include this repo in your weekly email.",
    )

    class Meta:
        unique_together = (("repo", "user"),)

    def __str__(self):
        return "<UserRepo(%s): %s, %s>" % (
            self.id,
            self.user.username,
            self.repo.full_name,
        )

    __repr__ = __str__


class ReleaseWatch(models.Model):
    repo = models.OneToOneField(Repo, on_delete=models.CASCADE)
    dev_branch = models.CharField(
        max_length=256,
        verbose_name="development branch",
        help_text="The branch that tracks the latest code (ie, where pull requests are merged to).",
    )

    DUAL_BRANCH = "DB"
    release_branch = models.CharField(
        max_length=256,
        blank=True,
        default="",
        help_text="The branch that tracks the most recent release.",
    )

    TAG_PATTERN = "TP"
    tag_pattern = models.CharField(
        max_length=256,
        blank=True,
        default=r"*.*.*",
        help_text=(
            "A shell pattern to match release tags."
            " The default matches 3-part semver."
            ' <a href="https://docs.python.org/2/library/fnmatch.html">More details</a>.'
        ),
    )

    CHOICES = (
        (DUAL_BRANCH, "dual branch"),
        (TAG_PATTERN, "tag pattern"),
    )
    style = models.CharField(
        max_length=2,
        choices=CHOICES,
    )

    exclude_pattern = models.CharField(
        max_length=256,
        blank=True,
        default="[!*]",
        help_text=(
            "A shell pattern to match commit messages that shouldn't count as a release."
            " The default matches nothing."
            ' <a href="https://docs.python.org/2/library/fnmatch.html">More details</a>.'
        ),
    )

    def __str__(self):
        return "<ReleaseWatch(%s): %s %s>" % (self.id, self.repo.full_name, self.style)

    __repr__ = __str__
