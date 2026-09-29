#!/bin/sh
set -eu
domain=$(sed -n 's/^DOMAIN=//p' /etc/opora-apk/production.env)
[ "${RENEWED_LINEAGE:-}" = "/etc/letsencrypt/live/$domain" ] || exit 0
install -m 0644 "$RENEWED_LINEAGE/fullchain.pem" /etc/opora-apk/tls/fullchain.pem
install -m 0600 "$RENEWED_LINEAGE/privkey.pem" /etc/opora-apk/tls/privkey.pem
/usr/local/sbin/opora-compose exec -T proxy nginx -t
/usr/local/sbin/opora-compose exec -T proxy nginx -s reload
