#!/usr/bin/env bash
# 8. Create a directory inside the project working directory.
# Usage: feature8.sh <name> [parent_folder]
# The working directory is the folder the tool is run from.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

create_directory() {
    local name=$1 parent=${2:-$WORK_DIR} path
    require_home_workdir || return 1
    if [[ -z $name ]]; then
        error directory.empty_name
        return 1
    fi
    if [[ ! $name =~ ^[A-Za-z0-9._-]+$ || $name == "." || $name == ".." ]]; then
        error directory.invalid_name "$name"
        return 1
    fi
    # The parent folder must exist and be inside the working directory.
    parent=$(realpath -e -- "$parent" 2>/dev/null)
    if [[ ! -d $parent ]] || ! is_inside_workdir "$parent"; then
        error directory.bad_parent "$WORK_DIR"
        return 1
    fi
    path="$parent/$name"
    if [[ -e $path ]]; then
        error directory.exists "$path"
        return 1
    fi
    if ! mkdir -- "$path"; then
        error directory.failed
        return 1
    fi
    t directory.created "$path"
    ls -ld -- "$path"
}

create_directory "$1" "$2"
