# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hmac
import json
import logging
from datetime import timedelta
from hashlib import sha1

from django import forms
from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.forms import modelform_factory
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from repominder.lib import ghapp, releases

from .models import Installation, ReleaseWatch, Repo, RepoInstall, UserRepo

logger = logging.getLogger(__name__)


def badge_info(request, selector):
    data = releases.decode_badge_selector(str(selector))
    releasewatch = Repo.objects.get(full_name=data["full_name"]).releasewatch

    diff = releases.ReleaseDiff.from_releasewatch(releasewatch)

    return JsonResponse({"status": "stale" if diff.has_changes else "fresh"})


@login_required()
def account(request):
    if request.GET.get("refresh"):
        logger.info("refresh requested")
        for installation in request.user.installation_set.all():
            ghapp.cache_install(installation)
        ghapp.cache_repos(request.user)
        # pop the querystring
        return redirect(account)
    elif request.user.profile.last_userrepo_refresh < timezone.now() - timedelta(
        days=1
    ):
        logger.info(
            "last refresh at %s; refreshing", request.user.profile.last_userrepo_refresh
        )
        ghapp.cache_repos(request.user)

    configured_repos = []
    watched_repos = []
    unconfigured_repos = []
    for userrepo in (
        request.user.userrepo_set.all()
        .order_by("repo__full_name")
        .select_related("repo", "repo__releasewatch")
    ):
        if userrepo.enable_digest and hasattr(userrepo.repo, "releasewatch"):
            watched_repos.append(userrepo.repo)
        elif not userrepo.enable_digest and hasattr(userrepo.repo, "releasewatch"):
            configured_repos.append(userrepo.repo)
        else:
            unconfigured_repos.append(userrepo.repo)
    c = {
        "GH_APP_NAME": settings.GH_APP_NAME,
        "configured_repos": configured_repos,
        "watched_repos": watched_repos,
        "unconfigured_repos": unconfigured_repos,
        "no_repos": not any([configured_repos, watched_repos, unconfigured_repos]),
    }

    return render(request, "logged_in.html", c)


@method_decorator(cache_control(public=True, max_age=3600), name="dispatch")
class CachedView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["GH_APP_NAME"] = settings.GH_APP_NAME
        context["cached_view"] = True  # base.html looks for this
        return context


class LoggedOutView(CachedView):
    template_name = "logged_out.html"


class PrivacyView(CachedView):
    template_name = "privacy.html"


@login_required()
def repo_details(request, id):
    repo = get_object_or_404(Repo, users__in=[request.user], id=id)
    try:
        releasewatch = repo.releasewatch
        style = releasewatch.style
    except ReleaseWatch.DoesNotExist:
        releasewatch = None
        # This can be in the querystring (from the style list) or form (from the hidden field).
        style = request.GET.get("style") or request.POST.get("style")

    c = {"repo": repo, "ReleaseWatch": ReleaseWatch}
    if not style:
        # Show the style list.
        return render(request, "repo.html", c)

    fields = ["dev_branch", "style"]
    if style == ReleaseWatch.DUAL_BRANCH:
        fields.append("release_branch")
    elif style == ReleaseWatch.TAG_PATTERN:
        fields.append("tag_pattern")
    else:
        raise SuspiciousOperation("unrecognized style")
    fields.append("exclude_pattern")

    # modify the fields on the generated form to include the digest checkbox.
    # this should maybe use a formset instead?
    userrepo = UserRepo.objects.get(user=request.user, repo=repo)
    WatchForm = modelform_factory(ReleaseWatch, fields=fields)
    WatchForm.base_fields["enable_digest"] = forms.BooleanField(
        initial=userrepo.enable_digest,
        required=False,
        label="Email notifications",
        help_text=UserRepo._meta.get_field("enable_digest").help_text,
    )

    if request.method == "GET":
        form = WatchForm(instance=releasewatch, initial={"style": style})
        form.fields["style"].widget = forms.HiddenInput()

        c["releasewatch"] = releasewatch
        c["watchform"] = form
        c["badge_url"] = releases.get_badge_url(request, releasewatch)
        c.update(csrf(request))
        return render(request, "repo.html", c)

    if request.method == "POST" and "delete" in request.POST:
        logger.info("deleting %s", releasewatch)
        releasewatch.delete()
        userrepo.enable_digest = False
        userrepo.save()
    elif request.method == "POST":
        post_data = request.POST.copy()
        form = WatchForm(post_data, instance=releasewatch)
        if form.is_valid():
            releasewatch = form.save(commit=False)
            releasewatch.repo = repo
            releasewatch.save()
            userrepo.enable_digest = form.cleaned_data["enable_digest"]
            userrepo.save()
        else:
            c["releasewatch"] = releasewatch
            c["watchform"] = form
            c["badge_url"] = releases.get_badge_url(request, releasewatch)
            c.update(csrf(request))
            return render(request, "repo.html", c)

    return redirect(account)


def logout(request):
    auth_logout(request)
    return redirect("/")


@require_POST
@csrf_exempt
def receive_hook(request):
    header_signature = request.META.get("HTTP_X_HUB_SIGNATURE")
    if header_signature is None:
        return HttpResponseForbidden("Permission denied.")
    sha_name, signature = header_signature.split("=")
    if sha_name != "sha1":
        return HttpResponseServerError("Operation not supported.", status=501)
    mac = hmac.new(
        force_bytes(settings.GH_APP_WEBHOOK_SECRET),
        msg=force_bytes(request.body),
        digestmod=sha1,
    )
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return HttpResponseForbidden("Permission denied.")

    event = request.META.get("HTTP_X_GITHUB_EVENT", "ping")
    data = json.loads(request.body)
    logger.info("received hook: %r", data)

    if event == "ping":
        return HttpResponse("pong")
    elif event == "installation":
        # install/uninstall: update install id + repos
        action = data["action"]
        installation_id = data["installation"]["id"]
        repo_details = data["repositories"]
        sender_login = data["sender"]["login"]
        if action == "created":
            installation, created = Installation.objects.get_or_create(
                installation_id=installation_id
            )
            try:
                user = User.objects.get(username=sender_login)
                installation.users.add(user)
            except User.DoesNotExist:
                # hook received before user logged in
                pass
            for detail in repo_details:
                repo, created = Repo.objects.get_or_create(
                    full_name=detail["full_name"]
                )
                if created:
                    logger.info("created", repo)
                repo.installations.add(installation)
        elif action == "deleted":
            logger.info("deleting %s", installation_id)
            Installation.objects.get(installation_id=installation_id).delete()
            repo_count = Repo.objects.filter(installations__isnull=True).delete()
            logger.info("deleted %s repos", repo_count)
        else:
            logger.warn(
                "unsupported installation action %r for install %s",
                action,
                installation_id,
            )
            return HttpResponseServerError("Operation not supported.", status=501)
        return HttpResponse(status=200)
    elif event == "installation_repositories":
        # repo add/remove: update repos
        action = data["action"]
        installation_id = data["installation"]["id"]
        if action == "removed":
            for detail in data["repositories_removed"]:
                logger.info(
                    "removing to link %s for %s", detail["full_name"], installation_id
                )
                RepoInstall.objects.get(
                    repo__full_name=detail["full_name"],
                    installation__installation_id=installation_id,
                ).delete()
            repo_count = Repo.objects.filter(installations__isnull=True).delete()
            logger.info("deleted %s orphaned repos", repo_count)
        else:
            logger.info(
                "removing to link %s for %s", detail["full_name"], installation_id
            )
            installation = Installation.objects.get(installation_id=installation_id)
            for detail in data["repositories_added"]:
                repo, created = Repo.objects.get_or_create(
                    full_name=detail["full_name"]
                )
                repo.installations.add(installation)
        return HttpResponse(status=200)

    logger.warn("received unexpected event %r", event)
    return HttpResponse(status=204)
