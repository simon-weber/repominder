import logging

from django.db import transaction
from github import Github

from repominder.apps.core.models import Repo, UserRepo

logger = logging.getLogger(__name__)


def cache_repos(user):
    # TODO this isn't really generic
    social = user.social_auth.get(provider='github-app')

    gh = Github(social.extra_data['access_token'])
    repos = gh.get_user().get_repos()
    current_names = {r.full_name for r in repos}

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
