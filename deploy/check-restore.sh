#!/bin/bash
set -euo pipefail
umask 077
DC=/usr/local/sbin/opora-compose
BACKUPS=/etc/opora-apk/backups
install -d -m 0700 "$BACKUPS"
[[ "$(readlink -f "$BACKUPS")" == "$BACKUPS" ]] || exit 1
exec 9>"$BACKUPS/.restore-check.lock"
flock -n 9 || { echo "Another restore check is running"; exit 1; }
STAMP=$(date -u +%Y%m%d%H%M%S)
DUMP="$BACKUPS/verified-$STAMP.dump"
RESTORE_DB="navigator_restore_$STAMP"
fingerprint() {
    "$DC" exec -T db psql -X -q -A -t -v ON_ERROR_STOP=1 -U navigator -d "$1" <<'SQL' | sha256sum | cut -d ' ' -f 1
SELECT format('SELECT %L, COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text), ''[]''::jsonb)::text FROM %I.%I t;', tablename, schemaname, tablename)
FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
\gexec
SQL
}
BEFORE=$(fingerprint navigator)
"$DC" exec -T db pg_dump -U navigator -d navigator -Fc > "$DUMP.partial"
test -s "$DUMP.partial"
"$DC" exec -T db pg_restore --list < "$DUMP.partial" > /dev/null
mv -- "$DUMP.partial" "$DUMP"
AFTER=$(fingerprint navigator)
if [[ "$BEFORE" != "$AFTER" ]]; then
    echo "Source database changed during backup; retained dump, verification must be retried"
    exit 1
fi
"$DC" exec -T db createdb -U navigator "$RESTORE_DB"
"$DC" exec -T db pg_restore -U navigator -d "$RESTORE_DB" --no-owner --exit-on-error < "$DUMP"
RESTORED=$(fingerprint "$RESTORE_DB")
if [[ "$BEFORE" != "$RESTORED" ]]; then
    echo "Restore mismatch; isolated restore database retained for investigation"
    exit 1
fi
"$DC" exec -T db psql -X -A -t -v ON_ERROR_STOP=1 -U navigator -d "$RESTORE_DB" -c 'SELECT version_num FROM alembic_version;'
printf 'Restore verified: all public tables SHA-256 %s\nBackup retained: %s\n' "$RESTORED" "$DUMP"
"$DC" exec -T db dropdb -U navigator "$RESTORE_DB"
