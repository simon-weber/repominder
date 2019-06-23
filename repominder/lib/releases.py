import base64
from collections import namedtuple
import fnmatch
import json
import logging
import re
import urllib.request, urllib.parse, urllib.error

import django
django.setup()

from django.urls import reverse
from github import Github

from repominder.apps.core.models import ReleaseWatch

BADGE_URL = 'https://img.shields.io/badge/dynamic/json.svg'

logger = logging.getLogger(__name__)


def get_badge_url(request, releasewatch):
    if not releasewatch:
        return

    selector = encode_badge_selector(releasewatch)
    uri = reverse('badge_info', kwargs={'selector': selector})
    params = [
        ('label', 'release'),
        ('query', '$.status'),
        ('maxAge', str(60 * 60 * 12)),  # 12 hrs
        ('uri', request.build_absolute_uri(uri)),
        ('link', request.build_absolute_uri('/')),
    ]

    url = "%s?%s" % (BADGE_URL, urllib.parse.urlencode(params))
    logger.info("%s selector, url: %s %s", releasewatch, selector, url)

    return url


def encode_badge_selector(releasewatch):
    return base64.urlsafe_b64encode(json.dumps({
        'user_id': releasewatch.userrepo.user.id,
        'repo_id': releasewatch.userrepo.repo.id,
    }))


def decode_badge_selector(selector):
    return json.loads(base64.urlsafe_b64decode(selector))


class ReleaseDiff(namedtuple('ReleaseDiff', ['repo_name', 'has_changes', 'compare_url'])):
    __slots__ = ()

    @staticmethod
    def from_releasewatch(releasewatch):
        user = releasewatch.userrepo.user
        social = user.social_auth.get(provider='github')
        token = social.extra_data['access_token']

        gh = Github(token)

        if releasewatch.style == ReleaseWatch.DUAL_BRANCH:
            return two_branch_diff(gh, releasewatch.userrepo.repo.full_name,
                                   releasewatch.release_branch, releasewatch.dev_branch, releasewatch.exclude_pattern)
        elif releasewatch.style == ReleaseWatch.TAG_PATTERN:
            return tag_pattern_diff(gh, releasewatch.userrepo.repo.full_name,
                                    releasewatch.tag_pattern, releasewatch.dev_branch, releasewatch.exclude_pattern)
        else:
            raise ValueError("unknown release style: %s" % releasewatch.style)


def all_commits_excluded(exclude_pattern, comparison):
    p = re.compile(fnmatch.translate(exclude_pattern))
    for ghcommit in comparison.commits:
        if not p.match(ghcommit.commit.message):
            logger.info("found unexcluded commit: %r matched %r", exclude_pattern, ghcommit.commit.message)
            return False
    return True


def two_branch_diff(gh, repo_full_name, base, head, exclude_pattern):
    # TODO unneeded request
    repo = gh.get_repo(repo_full_name)
    comparison = repo.compare(base, head)

    if comparison.ahead_by and not all_commits_excluded(exclude_pattern, comparison):
        return ReleaseDiff(repo_full_name, True, comparison.html_url)

    return ReleaseDiff(repo_full_name, False, None)


def tag_pattern_diff(gh, repo_full_name, tag_pattern, head, exclude_pattern):
    # note that this gets tags in gh order, then picks the first matching one.
    # this can choose an incorrect release since github returns them in alphabetical order,
    # but it's often the correct one.
    # I don't think there's really a good workaround to this. options are:
    #  * get all the tags, make n requests to the commit or tag api for their creation date
    #  * wait for the v4 api (which allows sorting on annotated tag date)
    #  * use the git api instead

    # TODO unneeded request
    repo = gh.get_repo(repo_full_name)

    p = re.compile(fnmatch.translate(tag_pattern))
    tag_name = None
    for tag in repo.get_tags():
        if p.match(tag.name):
            tag_name = tag.name
            logger.info("%s matched tag %s", repo_full_name, tag_name)
            break

    if tag_name:
        return two_branch_diff(gh, repo_full_name, tag_name, head, exclude_pattern)

    return ReleaseDiff(repo_full_name, False, None)
