#!/usr/bin/env bash

set -e

source .venv/bin/activate

db_path=$(echo "from django.conf import settings
print(settings.DATABASES['default']['NAME'])" \
  | python manage.py shell)
db_name=$(basename "${db_path}")
s3_path="repominder/$(date +'%Y-%m-%d_%X')_${db_name}"
backup_path="/tmp/${db_name}.bak"

sqlite3 "${db_path}" ".backup '${backup_path}'"
s3cmd --bucket-location=auto --host=https://$CF_ACCOUNT_ID.r2.cloudflarestorage.com --host-bucket=https://$CF_ACCOUNT_ID.r2.cloudflarestorage.com \
  put "${backup_path}" "s3://simoncodes-sqlite/${s3_path}"

wget https://hc-ping.com/${HC_ID_BACKUP} -nv -T 10 -t 5 -O /dev/null
