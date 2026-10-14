#!/usr/bin/env bash
# 9. File permissions for the owner of a file.
# Usage:
#   feature9.sh                      Creates the test file (if missing) and prints its path.
#   feature9.sh <file> read          Leaves the owner with read permission only.
#   feature9.sh <file> readwrite     Gives the owner read and write permission.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

TEST_FILE="$WORK_DIR/test_file.txt"

# Creates the test file if it does not exist yet.
prepare_test_file() {
    if [[ ! -e $TEST_FILE ]]; then
        {
            t permission.test_file_header
            t permission.test_file_created "$(date '+%Y-%m-%d %H:%M:%S')" "$(whoami)"
        } > "$TEST_FILE" || return 1
    fi
}

set_permissions() {
    local file=$1 mode=$2 permission
    require_home_workdir || return 1
    prepare_test_file || return 1
    if [[ -z $file ]]; then
        echo "$TEST_FILE"
        return 0
    fi
    # Only the owner bits change; the execute bit is kept as it was.
    case $mode in
        read)      permission="u+r,u-w" ;;
        readwrite) permission="u+rw" ;;
        *)
            error permission.invalid_mode "$mode"
            return 1
            ;;
    esac
    if [[ ! -f $file ]]; then
        error permission.not_a_file "$file"
        return 1
    fi
    file=$(realpath -- "$file")
    if ! is_inside_workdir "$file"; then
        error permission.outside_workdir "$WORK_DIR"
        return 1
    fi
    if [[ ! -O $file ]]; then
        error permission.not_owner "$file"
        return 1
    fi

    t permission.change
    t permission.before "$(ls -l -- "$file")"
    if ! chmod "$permission" -- "$file"; then
        error permission.chmod_failed
        return 1
    fi
    t permission.after "$(ls -l -- "$file")"
    t permission.octal "$(stat -c '%a' -- "$file")"
    echo

    t permission.check
    if cat -- "$file" > /dev/null 2>&1; then
        t permission.read_allowed
    else
        t permission.read_denied
    fi
    if [[ $file == "$TEST_FILE" ]]; then
        # On the test file the tool really tries to write.
        if { t permission.test_file_modified "$(date '+%Y-%m-%d %H:%M:%S')" >> "$file"; } 2>/dev/null; then
            t permission.write_allowed_test
        else
            t permission.write_denied_test
        fi
        echo
        t permission.content "$(basename -- "$file")"
        cat -- "$file"
    elif [[ -w $file ]]; then
        # Other files are only checked, so their content is never changed.
        t permission.write_allowed
    else
        t permission.write_denied
    fi
}

set_permissions "$1" "$2"
