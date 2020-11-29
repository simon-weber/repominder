import logging

from social_core.pipeline.partial import partial

default_app_config = "repominder.apps.core.apps.CoreConfig"

logger = logging.getLogger(__name__)


@partial
def cache_github_details(strategy, backend, request, details, *args, **kwargs):
    from repominder.lib import ghapp

    install_id = request.GET.get("installation_id")
    if install_id:
        logger.info("new/updated installation authed; refreshing repos")
        user = kwargs["user"]
        ghapp.cache_repos(user)
