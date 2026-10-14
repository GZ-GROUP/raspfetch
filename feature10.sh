#!/usr/bin/env bash
# 10. Diagnostic report: saves a summary of the system status to a text file.
# It reuses the other diagnostic scripts, which must be in the same folder.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

REPORT_FILE="$WORK_DIR/diagnostic_report.txt"

# Runs another feature script without gauge lines, so they stay out of the report.
run_feature() {
    RASPFETCH_TUI=0 bash "$SCRIPTS_DIR/feature$1.sh"
}

diagnostic_report() {
    require_home_workdir || return 1
    if [[ -e $REPORT_FILE && ! -w $REPORT_FILE ]]; then
        error report.not_writable "$REPORT_FILE"
        return 1
    fi
    {
        t report.title
        t report.date "$(date '+%Y-%m-%d %H:%M:%S')"
        t report.user "$(whoami)"
        t report.host "$(hostname)"
        echo
        t report.system
        run_feature 1
        echo
        t report.memory
        run_feature 2
        echo
        t report.storage
        run_feature 3
        echo
        t report.network
        run_feature 4
        echo
        t report.temperature
        run_feature 6
        echo
        t report.processes "$(ps -e --no-headers | wc -l)"
    } > "$REPORT_FILE"
    t report.saved "$REPORT_FILE"
    echo
    cat -- "$REPORT_FILE"
}

diagnostic_report
