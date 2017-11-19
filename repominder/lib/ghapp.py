import logging
import requests

from django.db import transaction

from repominder.apps.core.models import Repo, UserRepo

logger = logging.getLogger(__name__)


def get_session():
    """Return a requests.Session for use with the apps api."""

    return requests.Session()


def set_auth(session, installation_token):
    session.headers.update({'Authorization': "token %s" % installation_token})


def cache_repos(user):
    # TODO this isn't really generic
    social = user.social_auth.get(provider='github')

    s = get_session()
    set_auth(s, social.extra_data['access_token'])
    res = s.get("https://api.github.com/users/%s/repos" % social.extra_data['login'])
    res.raise_for_status()
    current_names = {repo['full_name'] for repo in res.json()}

    # bulk create/update repos, then bulk create/update links for this user
    with transaction.atomic():
        cached_names = set(Repo.objects.filter(full_name__in=current_names).values_list('full_name', flat=True))
        new_names = current_names - cached_names
        new_repos = [Repo(full_name=name) for name in new_names]
        if new_repos:
            logger.info("creating repos: %r", new_repos)
            Repo.objects.bulk_create(new_repos)

        new_ids = Repo.objects.filter(full_name__in=new_names).values_list('id', flat=True)
        new_links = [UserRepo(repo_id=id, user=user) for id in new_ids]
        if new_links:
            logger.info("creating links: %r", new_links)
            UserRepo.objects.bulk_create(new_links)
