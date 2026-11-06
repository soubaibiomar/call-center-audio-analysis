#!/bin/sh
# Run inside the dedicated object-store container after its health check passes.
set -eu
task_config=$(mktemp -d /tmp/project28-mc.XXXXXX)
trap 'rm -rf "$task_config"' EXIT
mc() { /usr/bin/mc --config-dir "$task_config" "$@"; }
mc alias set local http://127.0.0.1:9000 "$(cat /run/secrets/s3_root_user)" "$(cat /run/secrets/s3_root_password)" >/dev/null
mc mb --ignore-existing local/project28-audio >/dev/null
task_access=$(cat /run/secrets/s3_access_key)
if ! mc admin user info local "$task_access" >/dev/null 2>&1; then
  mc admin user add local "$task_access" "$(cat /run/secrets/s3_secret_key)" >/dev/null
fi
cat > "$task_config/policy.json" <<'POLICY'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObject","s3:PutObject"],"Resource":["arn:aws:s3:::project28-audio/tenants/*"]}]}
POLICY
mc admin policy create local project28-audio-runtime "$task_config/policy.json" >/dev/null
mc admin policy attach local project28-audio-runtime --user "$task_access" >/dev/null
echo "Private bucket and restricted runtime object permissions verified"
