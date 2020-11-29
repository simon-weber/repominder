import logging
import time

import jwt
import requests
from django.conf import settings
from django.utils import timezone
from github import Github

from repominder.apps.core.models import Repo, UserRepo

logger = logging.getLogger(__name__)


def cache_repos(user):
    # should only be run as a result of a user logging in (ie, not from a cron or script)
    social = user.social_auth.get(provider="github-app")

    # user access token
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


def get_app_url(app_name):
    return "https://github.com/apps/%s" % app_name


def get_session():
    """Return a requests.Session for use with the apps api."""

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


def test(installation):
    # social = user.social_auth.get(provider='github-app')

    s = get_session()
    token = get_installation_token(
        installation, settings.GH_APP_ID, settings.GH_APP_PEM
    )
    set_installation_auth(s, token)
    res = s.get("https://api.github.com/installation/repositories")

    res.raise_for_status()
    # current_names = {repo['full_name'] for repo in res.json()}

    # # bulk create/update repos, then bulk create/update links for this user
    # with transaction.atomic():
    #     cached_names = set(Repo.objects.filter(full_name__in=current_names).values_list('full_name', flat=True))
    #     new_names = current_names - cached_names
    #     new_repos = [Repo(full_name=name) for name in new_names]
    #     if new_repos:
    #         logger.info("creating repos: %r", new_repos)
    #         Repo.objects.bulk_create(new_repos)

    #     new_ids = Repo.objects.filter(full_name__in=new_names).values_list('id', flat=True)
    #     new_links = [UserRepo(repo_id=id, user=user) for id in new_ids]
    #     if new_links:
    #         logger.info("creating links: %r", new_links)
    #         UserRepo.objects.bulk_create(new_links)


# def hook(data):
# 	header_signature = request.headers.get('X-Hub-Signature')
# 	if header_signature is None:
# 		abort(403)
#
# 	sha_name, signature = header_signature.split('=')
# 	if sha_name != 'sha1':
# 		abort(501)
#
# 	# HMAC requires the key to be bytes, but data is string
# 	mac = hmac.new(str(secret), msg=request.data, digestmod='sha1')
#
# 	# Python prior to 2.7.7 does not have hmac.compare_digest
# 	if hexversion >= 0x020707F0:
# 		if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
# 			abort(403)
# 	else:
# 		# What compare_digest provides is protection against timing
# 		# attacks; we can live without this protection for a web-based
# 		# application
# 		if not str(mac.hexdigest()) == str(signature):
# 			abort(403)
