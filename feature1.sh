#!/usr/bin/env bash
# 1. System information: hostname, kernel version and uptime.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

system_info() {
    t system.hostname "$(hostname)"
    t system.kernel "$(uname -r)"
    t system.arch "$(uname -m)"
    t system.uptime "$(uptime -p | sed 's/^up //')"
    t system.boot "$(uptime -s)"
}

system_info
