import logging

from django.conf import settings
from django.dispatch.dispatcher import receiver
from django_amazon_ses import pre_send, post_send

logger = logging.getLogger(__name__)


@receiver(pre_send)
def set_reply_to(sender, message=None, **kwargs):
    if message:
        if message.reply_to:
            logger.warning("overriding reply_to of %r", message.reply_to)

        message.reply_to = [settings.NOREPLY_ADDRESS]


@receiver(post_send)
def log_message(sender, message=None, message_id=None, **kwargs):
    if message and message_id:
        logger.info("sent email to %r: id %s", message.to, message_id)
    else:
        logger.warning("post_send didn't include message info: %r, %r",
                       message, message_id)
