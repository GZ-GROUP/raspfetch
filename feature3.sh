#!/usr/bin/env bash
# 3. Storage check: used and available space on the file systems.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

storage_check() {
    local size used available percent
    read -r size used available percent < <(LC_ALL=C df -hP / | awk 'NR == 2 {print $2, $3, $4, $5}')
    t storage.root
    t storage.used "$used" "$size" "$percent"
    t storage.available "$available"
    emit_gauge disk "$used" "$size" "${percent%\%}"
    echo
    # Virtual file systems are skipped to keep the table readable.
    df -h -x tmpfs -x devtmpfs -x squashfs
}

storage_check
