import logging
import time

import jwt
import requests
from django.conf import settings
from django.utils import timezone
from github import Github

from repominder.apps.core.models import Repo, RepoInstall, UserRepo

logger = logging.getLogger(__name__)


def cache_install(installation):
    # sync installation/repo access state
    # should be kept up to date with hooks, but may need to be run manually if a hook is dropped
    res = get_installation_repos(installation)

    RepoInstall.objects.filter(installation=installation).delete()
    for detail in res.json()["repositories"]:
        repo, created = Repo.objects.get_or_create(full_name=detail["full_name"])
        repo.installations.add(installation)

    to_delete = Repo.objects.filter(installations__isnull=True)
    if to_delete:
        print("deleting", to_delete)
        to_delete.delete()


def cache_repos(user):
    # sync user/repo access state
    # not kept up to date with hooks, needs to be run periodically
    # should only be run as a result of a user logging in (ie, not from a cron or script)
    social = user.social_auth.get(provider="github-app")

    # this is a user access token
    gh = Github(social.extra_data["access_token"])
    repos = gh.get_user().get_repos()
    accessible_names = [
        r.full_name for r in repos if r.permissions.push or r.permissions.admin
    ]
    UserRepo.objects.filter(user=user).exclude(
        repo__full_name__in=accessible_names
    ).delete()
    for repo in Repo.objects.filter(full_name__in=accessible_names):
        repo.users.add(user)

    user.profile.last_userrepo_refresh = timezone.now()
    user.profile.save()


def get_session():
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github.v3+json"})
    return s


def set_app_auth(session, app_token):
    session.headers.update({"Authorization": "Bearer %s" % app_token})


def set_installation_auth(session, installation_token):
    session.headers.update({"Authorization": "token %s" % installation_token})


def build_app_token(iss, key_contents, iat=None, exp=None):
    """Return a JWT to auth as ourselves.

    Does not make any external requests.

    See:
    https://developer.github.com/apps/building-integrations/setting-up-and-registering-github-apps/about-authentication-options-for-github-apps/
    """
    epoch_secs = int(time.time())

    if iat is None:
        iat = epoch_secs

    if exp is None:
        exp = iat + (10 * 60)

    payload = {
        "iat": iat,
        "exp": exp,
        "iss": iss,
    }

    return jwt.encode(payload, key_contents, algorithm="RS256").decode("utf-8")


def get_installation_token_details(installation_id, app_token):
    """Return the response from requesting a new installation token, a dict with keys 'token' and 'expires_at'.

    See:
    https://developer.github.com/apps/building-integrations/setting-up-and-registering-github-apps/about-authentication-options-for-github-apps/
    """

    url = "https://api.github.com/app/installations/%s/access_tokens" % installation_id
    s = get_session()
    r = s.post(url, headers={"Authorization": "Bearer %s" % app_token})

    r.raise_for_status()

    return r.json()


def get_installation_token(installation, app_id, pem_contents):
    """Return an installation token by using an app token and stored installation id."""

    s = get_session()
    installation_id = installation.installation_id
    app_token = build_app_token(app_id, pem_contents)
    set_app_auth(s, app_token)
    i_token_details = get_installation_token_details(installation_id, app_token)

    return i_token_details["token"]


def get_installation_repos(installation):
    s = get_session()
    token = get_installation_token(
        installation, settings.GH_APP_ID, settings.GH_APP_PEM
    )
    set_installation_auth(s, token)
    res = s.get("https://api.github.com/installation/repositories")

    res.raise_for_status()

    return res
