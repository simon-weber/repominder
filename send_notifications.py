import logging
from collections import defaultdict

import django

django.setup()

from django.core.mail import EmailMessage  # noqa: E402

from repominder.apps.core.models import UserRepo  # noqa: E402
from repominder.lib.releases import ReleaseDiff  # noqa: E402

logger = logging.getLogger("repominder.send_notifications")


def send_email(user, diffs):
    with_changes, without_changes = [], []
    for diff in diffs:
        (with_changes if diff.has_changes else without_changes).append(diff)

    if not with_changes:
        return

    lines = ["Repominder noticed unreleased changes on the following projects:"]
    for diff in with_changes:
        lines.append("  * %s: %s" % (diff.repo_name, diff.compare_url))

    if without_changes:
        lines.append("\n")
        lines.append("The following projects are up to date:")
        for diff in without_changes:
            lines.append("  * %s" % diff.repo_name)

    lines.append("\n")
    lines.append("To configure your reminders, log in at https://www.repominder.com")
    lines.append("\n")
    lines.append(
        "Appreciate Repominder? Consider sponsoring development! https://github.com/sponsors/simon-weber"
    )

    email = EmailMessage(
        subject="unreleased changes detected",
        to=[user.email],
        body="\n".join(lines),
    )
    email.send(fail_silently=False)


if __name__ == "__main__":
    try:
        logger.info("running")
        user_diffs = defaultdict(list)  # user: [ReleaseDiff]

        for userrepo in UserRepo.objects.filter(enable_digest=True):
            releasewatch = userrepo.repo.releasewatch
            try:
                logger.info("checking: %s", releasewatch)
                diff = ReleaseDiff.from_releasewatch(releasewatch)

                logger.info("diff: %s", diff)
                user_diffs[userrepo.user].append(diff)
            except:
                logger.exception("failed to check diff for %s", releasewatch)

        for user, diffs in user_diffs.items():
            try:
                send_email(user, diffs)
            except:
                logger.exception("failed to send email for %s", releasewatch)

        logger.info("done")
    except:
        logger.exception("failed to send notifications")
