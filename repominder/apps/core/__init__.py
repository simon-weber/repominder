import logging

from social_core.pipeline.partial import partial

default_app_config = "repominder.apps.core.apps.CoreConfig"

logger = logging.getLogger(__name__)

# These happen during every login.


@partial
def cache_github_details(strategy, backend, request, details, *args, **kwargs):
    pass
