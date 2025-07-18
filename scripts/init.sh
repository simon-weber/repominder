#!/usr/bin/env bash

set -e

chmod 770 /opt/repominder

source .venv/bin/activate
python manage.py collectstatic -c --noinput

python manage.py migrate --noinput
echo "from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJ_SUPERUSER}', is_superuser=True):
  print(User.objects.create_superuser('${DJ_SUPERUSER}', '${DJ_SUPERUSER_EMAIL}', '${DJ_SUPERUSER_PASSWORD}'))" \
  | python manage.py shell

echo "from django.contrib.sites.models import Site;
s = Site.objects.get_current();
s.domain = '${SITE}';
s.name = 'repominder';
s.save();
print(Site.objects.get_current())" \
  | python manage.py shell
