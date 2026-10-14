#!/usr/bin/env bash
# Shared code for every featureN.sh: message translation (i18n) and helpers.
# Each script loads it with:  source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
#
# Language: set RASPFETCH_LANG (for example RASPFETCH_LANG=es). Default: English.
# Messages live in locales/<language>.lang as key=text lines.

SCRIPTS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOCALES_DIR="$SCRIPTS_DIR/locales"
DEFAULT_LANGUAGE="en"
WORK_DIR="$(pwd -P)"
HOME_DIR="$(realpath -- "$HOME")"

declare -A MESSAGES

# Loads a key=text catalog into MESSAGES; keys already loaded are overwritten.
load_messages() {
    local file=$1 line
    [[ -r $file ]] || return 1
    while IFS= read -r line || [[ -n $line ]]; do
        [[ -z $line || $line == \#* || $line != *=* ]] && continue
        MESSAGES[${line%%=*}]=${line#*=}
    done < "$file"
}

# English is always loaded first so a missing translation falls back to it.
load_messages "$LOCALES_DIR/$DEFAULT_LANGUAGE.lang"
if [[ -n $RASPFETCH_LANG && $RASPFETCH_LANG != "$DEFAULT_LANGUAGE" ]]; then
    load_messages "$LOCALES_DIR/$RASPFETCH_LANG.lang"
fi

# Prints a translated message: t <key> [one argument per %s]
t() {
    local key=$1
    shift
    # shellcheck disable=SC2059  # the catalog entry is the format string
    printf -- "${MESSAGES[$key]:-$key}\n" "$@"
}

# Prints a translated error message to stderr: error <key> [arguments]
error() {
    local key=$1
    shift
    echo "${MESSAGES[error.prefix]}: $(t "$key" "$@")" >&2
}

# Fails when the working directory is outside the user's home directory.
require_home_workdir() {
    if [[ $WORK_DIR != "$HOME_DIR" && $WORK_DIR != "$HOME_DIR"/* ]]; then
        error error.outside_home "$HOME_DIR" "$WORK_DIR"
        return 1
    fi
}

# Succeeds when the absolute path $1 is the working directory or inside it.
is_inside_workdir() {
    [[ $1 == "$WORK_DIR" || $1 == "$WORK_DIR"/* ]]
}

# Prints a machine-readable line for the gauges of main.py.
# Only active when main.py runs the script (it sets RASPFETCH_TUI=1).
emit_gauge() {
    if [[ ${RASPFETCH_TUI:-0} == 1 ]]; then
        echo "@gauge $*"
    fi
}
