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
from django.views.decorators.csrf import csrf_exempt

from repominder.lib import ghapp, releases
from .models import UserRepo, ReleaseWatch, Installation, Repo, RepoInstall

logger = logging.getLogger(__name__)


def badge_info(request, selector):
    data = releases.decode_badge_selector(str(selector))
    releasewatch = Repo.objects.get(full_name=data['full_name']).releasewatch

    diff = releases.ReleaseDiff.from_releasewatch(releasewatch)

    return JsonResponse({'status': 'stale' if diff.has_changes else 'fresh'})


@login_required(login_url='/')
def account(request):
    # if request.GET.get('refresh'):
    #     logger.info("refreshing")
    ghapp.cache_repos(request.user)
    print('repos', list(Repo.objects.all()))
    print('installs', list(Installation.objects.all()))
    print('repoinstalls', list(RepoInstall.objects.all()))

    releasewatches = []
    unwatched_repos = []
    for userrepo in request.user.userrepo_set.all().order_by('repo__full_name').select_related('repo', 'repo__releasewatch'):
        try:
            releasewatches.append(userrepo.repo.releasewatch)
        except ReleaseWatch.DoesNotExist:
            unwatched_repos.append(userrepo.repo)
    c = {
        'repos': unwatched_repos,
        'releasewatches': releasewatches,
    }

    return render(request, 'logged_in.html', c)


def landing(request):
    return render(request, 'logged_out.html')


@login_required(login_url='/')
def repo_details(request, id):
    repo = Repo.objects.get(users__in=[request.user], id=id)
    try:
        releasewatch = repo.releasewatch
        style = releasewatch.style
    except ReleaseWatch.DoesNotExist:
        releasewatch = None
        # This can be in the querystring (from the style list) or form (from the hidden field).
        style = request.GET.get('style') or request.POST.get('style')

    c = {'repo': repo, 'ReleaseWatch': ReleaseWatch}
    if not style:
        # Show the style list.
        return render(request, 'repo.html', c)

    fields = ['dev_branch', 'style']
    if style == ReleaseWatch.DUAL_BRANCH:
        fields.append('release_branch')
    elif style == ReleaseWatch.TAG_PATTERN:
        fields.append('tag_pattern')
    else:
        raise SuspiciousOperation("unrecognized style")
    fields.append('exclude_pattern')

    WatchForm = modelform_factory(ReleaseWatch, fields=fields)

    if request.method == 'GET':
        form = WatchForm(instance=releasewatch, initial={'style': style})
        form.fields['style'].widget = forms.HiddenInput()

        c['releasewatch'] = releasewatch
        c['watchform'] = form
        c['badge_url'] = releases.get_badge_url(request, releasewatch)
        c.update(csrf(request))
        return render(request, 'repo.html', c)

    if request.method == 'POST' and 'delete' in request.POST:
        logger.info("deleting %s", releasewatch)
        releasewatch.delete()
    elif request.method == 'POST':
        form = WatchForm(request.POST, instance=releasewatch)
        if form.is_valid():
            releasewatch = form.save(commit=False)
            releasewatch.repo = repo
            releasewatch.save()

    return redirect(account)


def logout(request):
    auth_logout(request)
    return redirect('/')

from django.http import HttpResponse
from django.views.decorators.http import require_POST
import json


@require_POST
@csrf_exempt
def receive_hook(request):
    # TODO validate secret and IP, https://simpleisbetterthancomplex.com/tutorial/2016/10/31/how-to-handle-github-webhooks-using-django.html
    event = request.META.get('HTTP_X_GITHUB_EVENT', 'ping')
    data = json.loads(request.body)
    import pprint
    pprint.pprint(data)
    print('got', event)
    print('pre hook')
    print('repos', list(Repo.objects.all()))
    print('installs', list(Installation.objects.all()))
    print('repoinstalls', list(RepoInstall.objects.all()))


    # TODO
    # install/uninstall: update install id + repos
    # repo add/remove: update repos
    if event == 'ping':
        return HttpResponse('pong')
    elif event == 'installation':
        # sync repos + install state
        # TODO can probably transaction + bulk this like userrepos
        action = data['action']
        installation_id = data['installation']['id']
        repo_details = data['repositories']
        if action == 'created':
            installation, created = Installation.objects.get_or_create(installation_id=installation_id)
            for detail in repo_details:
                print('handle', detail)
                repo, created = Repo.objects.get_or_create(full_name=detail['full_name'])
                print(repo, created)
                repo.installations.add(installation)
        elif action == 'deleted':
            Installation.objects.get(installation_id=installation_id).delete()
            Repo.objects.filter(installations__isnull=True).delete()
        else:
            logger.warn('unsupported installation action %r for install %s', action, installation_id)
            return HttpResponse(status=204)

    elif event == 'installation_repositories':
        action = data['action']
        installation_id = data['installation']['id']
        if action == 'removed':
            for detail in data['repositories_removed']:
                RepoInstall.objects.get(repo__full_name=detail['full_name'], installation__installation_id=installation_id).delete()
            to_delete = Repo.objects.filter(installations__isnull=True)
            if to_delete:
                print('deleting', to_delete)
                to_delete.delete()
        else:
            installation = Installation.objects.get(installation_id=installation_id)
            for detail in data['repositories_added']:
                repo, created = Repo.objects.get_or_create(full_name=detail['full_name'])
                repo.installations.add(installation)

    elif event == 'push':
        # push: update releasewatch if config changed
        return HttpResponse('success')

    print('post hook')
    print('repos', list(Repo.objects.all()))
    print('installs', list(Installation.objects.all()))
    print('repoinstalls', list(RepoInstall.objects.all()))

    # In case we receive an event that's neither a ping or push
    return HttpResponse(status=204)
