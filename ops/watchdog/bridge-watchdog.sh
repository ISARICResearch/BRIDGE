#!/usr/bin/env bash
set -euo pipefail

LOG_TAG="bridge-watchdog"
STATE_DIR="${STATE_DIR:-/var/tmp/bridge-watchdog}"
FAIL_FILE="${STATE_DIR}/failures"
ACTION_FILE="${STATE_DIR}/action"
LOCK_DIR="/run/${LOG_TAG}.lock"

IMDS_TIMEOUT="${IMDS_TIMEOUT:-5}"
APP_TIMEOUT="${APP_TIMEOUT:-10}"
FAIL_RESTART="${FAIL_RESTART:-5}"
FAIL_REBOOT="${FAIL_REBOOT:-10}"
APP_URL="${APP_URL:-http://127.0.0.1/}"

mkdir -p "${STATE_DIR}"

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    exit 0
fi
trap 'rmdir "${LOCK_DIR}"' EXIT

read_file_or_default() {
    local path="$1"
    local default_value="$2"

    if [[ -f "${path}" ]]; then
        cat "${path}"
    else
        printf '%s\n' "${default_value}"
    fi
}

check_imds() {
    local token

    token="$(
        curl -fsS -m "${IMDS_TIMEOUT}" -X PUT \
            -H "X-aws-ec2-metadata-token-ttl-seconds: 60" \
            http://169.254.169.254/latest/api/token
    )" || return 1

    curl -fsS -m "${IMDS_TIMEOUT}" \
        -H "X-aws-ec2-metadata-token: ${token}" \
        http://169.254.169.254/latest/meta-data/instance-id >/dev/null
}

check_app() {
    curl -fsS -m "${APP_TIMEOUT}" "${APP_URL}" >/dev/null
}

count="$(read_file_or_default "${FAIL_FILE}" "0")"
action="$(read_file_or_default "${ACTION_FILE}" "none")"

if check_imds && check_app; then
    printf '0\n' > "${FAIL_FILE}"
    printf 'none\n' > "${ACTION_FILE}"
    exit 0
fi

count="$(( count + 1 ))"
printf '%s\n' "${count}" > "${FAIL_FILE}"
logger -t "${LOG_TAG}" \
    "health check failed (${count}/${FAIL_REBOOT}); action=${action}; app_url=${APP_URL}"

if (( count >= FAIL_RESTART )) && [[ "${action}" == "none" ]]; then
    logger -t "${LOG_TAG}" \
        "restarting systemd-networkd after ${count} consecutive failures"
    printf 'restarted-network\n' > "${ACTION_FILE}"
    systemctl restart systemd-networkd || true
    exit 0
fi

if (( count >= FAIL_REBOOT )); then
    logger -t "${LOG_TAG}" \
        "rebooting after ${count} consecutive failures"
    systemctl reboot
fi
