from django.conf import settings

from mailchimp3 import MailChimp


client = MailChimp(
    settings.MAILCHIMP_API_USER, settings.MAILCHIMP_API_KEY,
    timeout=10.0,
    request_headers={'User-Agent': 'repominder-django (support@repominder.com)'}
)


def add_to_list(email, list_id):
    client.lists.members.create(list_id, {
        'email_address': email,
        'status': 'subscribed',
    })
