import logging

from django.conf import settings
import requests
from social_core.pipeline.partial import partial

default_app_config = 'repominder.apps.core.apps.CoreConfig'

logger = logging.getLogger(__name__)

# These happen during every login.


@partial
def cache_github_details(strategy, backend, request, details, *args, **kwargs):
    from repominder.lib import ghapp
    pass

    # install_id = request.GET.get('installation_id')
    # if install_id:
    #     # coming from new/updated installation
    #     pass
    #     print("install id", install_id)
    #     obj, created = Installation.objects.update_or_create(
    #         user=user, defaults={'installation_id': installation_id}
    #     )
    # else:
    #     # coming from website login
    #     user = kwargs['user']
    #     ghapp.cache_repos(user)


@partial
def subscribe_to_list(strategy, backend, request, details, *args, **kwargs):
    from repominder.lib import mailchimp

    user = kwargs['user']

    if user.last_login is not None:
        # Only add during the very first login.
        return

    if settings.DEBUG:
        logger.info("not adding email to mailchimp while DEBUG is on: %s", user.email)
        return

    try:
        mailchimp.add_to_list(user.email, settings.MAILCHIMP_LIST_ID)
    except requests.exceptions.HTTPError as err:
        if 'already a list member' not in err.response.text:
            logger.exception("did not add (or readd) to mailchimp: %s", user.email)
