# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django import forms
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.context_processors import csrf

from repominder.lib import ghapp, releases
from .models import UserRepo, ReleaseWatch

logger = logging.getLogger(__name__)


def badge_info(request, selector):
    data = releases.decode_badge_selector(str(selector))
    releasewatch = ReleaseWatch.objects.get(userrepo__user=data['user_id'], userrepo__repo=data['repo_id'])

    diff = releases.ReleaseDiff.from_releasewatch(releasewatch)

    return JsonResponse({'status': 'stale' if diff.has_changes else 'fresh'})


@login_required(login_url='/')
def account(request):
    if request.GET.get('refresh'):
        logger.info("refreshing")
        ghapp.cache_repos(request.user)

    unwatched_userrepos = []
    releasewatches = []
    for userrepo in request.user.userrepo_set.all().order_by('repo__full_name'):
        try:
            releasewatches.append(userrepo.releasewatch)
        except ReleaseWatch.DoesNotExist:
            unwatched_userrepos.append(userrepo)
    c = {
        'userrepos': unwatched_userrepos,
        'releasewatches': releasewatches,
    }

    return render(request, 'logged_in.html', c)


def landing(request):
    return render(request, 'logged_out.html')


@login_required(login_url='/')
def userrepo_details(request, id):
    userrepo = UserRepo.objects.get(user=request.user, id=id)
    try:
        releasewatch = userrepo.releasewatch
        style = releasewatch.style
    except ReleaseWatch.DoesNotExist:
        releasewatch = None
        # This can be in the querystring (from the style list) or form (from the hidden field).
        style = request.GET.get('style') or request.POST.get('style')

    c = {'userrepo': userrepo, 'ReleaseWatch': ReleaseWatch}
    if not style:
        # Show the style list.
        return render(request, 'userrepo.html', c)

    fields = ['dev_branch', 'style']
    if style == ReleaseWatch.DUAL_BRANCH:
        fields.append('release_branch')
    elif style == ReleaseWatch.TAG_PATTERN:
        fields.append('tag_pattern')
    else:
        raise SuspiciousOperation("unrecognized style")

    WatchForm = modelform_factory(ReleaseWatch, fields=fields)

    if request.method == 'GET':
        form = WatchForm(instance=releasewatch, initial={'style': style})
        form.fields['style'].widget = forms.HiddenInput()

        c['releasewatch'] = releasewatch
        c['watchform'] = form
        c['badge_url'] = releases.get_badge_url(request, releasewatch)
        c.update(csrf(request))
        return render(request, 'userrepo.html', c)

    if request.method == 'POST' and 'delete' in request.POST:
        logger.info("deleting %s", releasewatch)
        releasewatch.delete()
    elif request.method == 'POST':
        form = WatchForm(request.POST, instance=releasewatch)
        if form.is_valid():
            releasewatch = form.save(commit=False)
            releasewatch.userrepo = userrepo
            releasewatch.save()

    return redirect(account)


def logout(request):
    auth_logout(request)
    return redirect('/')
