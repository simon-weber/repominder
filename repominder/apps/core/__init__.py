import logging

from social_core.pipeline.partial import partial

default_app_config = "repominder.apps.core.apps.CoreConfig"

logger = logging.getLogger(__name__)


@partial
def cache_github_details(strategy, backend, request, details, *args, **kwargs):
    from repominder.apps.core.models import Installation, Profile
    from repominder.lib import ghapp

    user = kwargs["user"]
    Profile.objects.get_or_create(user=user)

    installation_id = request.GET.get("installation_id")
    if installation_id:
        installation, created = Installation.objects.get_or_create(
            installation_id=installation_id
        )
        installation.users.add(user)

        logger.info("new/updated installation authed; refreshing repos")
        ghapp.cache_repos(user)
