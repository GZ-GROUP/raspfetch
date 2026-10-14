#!/usr/bin/env bash
# 7. Active processes and their resource usage.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

active_processes() {
    t process.count "$(ps -e --no-headers | wc -l)"
    t process.load "$(cut -d ' ' -f 1-3 /proc/loadavg)"
    echo
    t process.top_cpu
    ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -n 11
    echo
    t process.top_memory
    ps -eo pid,user,%cpu,%mem,comm --sort=-%mem | head -n 6
}

active_processes
