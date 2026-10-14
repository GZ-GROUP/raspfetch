#!/usr/bin/env bash
# 2. Memory check: total, used and available RAM.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

memory_check() {
    local total used available percent
    # LC_ALL=C keeps the row name "Mem:" whatever the system language is.
    read -r total used available < <(LC_ALL=C free -m | awk '/^Mem:/ {print $2, $3, $7}')
    percent=$(( used * 100 / total ))
    t memory.total "$total"
    t memory.used "$used" "$total" "$percent"
    t memory.available "$available"
    emit_gauge mem "$used" "$total" "$percent"
    echo
    free -h
}

memory_check
