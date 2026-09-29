#!/bin/bash
set -euo pipefail
umask 077
OPS=/etc/opora-apk/deploy-20260928
DC=/usr/local/sbin/opora-compose
cd /opt/opora-apk
sha256sum -c --quiet /tmp/r3-SHA256.txt
docker tag opora-apk-production-app opora-apk-rollback:20260927-r3
cat > "$OPS/rollback.sh" <<'ROLLBACK'
#!/bin/bash
set -euo pipefail
umask 077
OPS=/etc/opora-apk/deploy-20260928
DC=/usr/local/sbin/opora-compose
cd /opt/opora-apk
$DC stop app worker
$DC exec -T db pg_dump -U navigator -d navigator -Fc > "$OPS/pre-rollback-$(date -u +%Y%m%d%H%M%S).dump"
docker tag opora-apk-rollback:20260927-r3 opora-apk-production-app
$DC up -d --no-build --force-recreate --wait app worker
$DC exec -T proxy nginx -s reload
echo 'Application rolled back; current database and new user data retained. No downgrade or old dump restore performed.'
ROLLBACK
chmod 700 "$OPS/rollback.sh"
$DC stop app worker
trap 'echo "Deployment failed; app/worker may be stopped. Use /etc/opora-apk/deploy-20260928/rollback.sh; never restore an old dump over current data."' ERR
bash deploy/check-restore.sh > "$OPS/final-backup-report.txt"
cat "$OPS/final-backup-report.txt"
python3 "$OPS/deploy_db_audit.py" navigator before "$OPS/pre-switch-rows.json"
python3 "$OPS/deploy_source_switch.py"
docker tag opora-apk-deploy:20260928 opora-apk-production-app
$DC up -d --no-build --force-recreate --wait app worker
$DC exec -T proxy nginx -s reload
$DC exec -T app alembic -c backend/alembic.ini current
$DC exec -T app alembic -c backend/alembic.ini check
python3 "$OPS/deploy_db_audit.py" navigator exact "$OPS/pre-switch-rows.json"
sha256sum -c --quiet "$OPS/SOURCE-SHA256.txt"
echo 'Deployment and preservation checks PASS'
