#!/usr/bin/env bash
# 5. Connectivity test: checks whether another host on the LAN replies.
# Usage: feature5.sh <ip>
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

# Succeeds when $1 is a valid IPv4 address (four numbers from 0 to 255).
is_valid_ipv4() {
    local ip=$1 octet
    local -a octets
    [[ $ip =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || return 1
    IFS=. read -ra octets <<< "$ip"
    for octet in "${octets[@]}"; do
        (( 10#$octet <= 255 )) || return 1
    done
}

connectivity_test() {
    local ip=$1
    if [[ -z $ip ]]; then
        error ping.missing_ip
        return 1
    fi
    if ! is_valid_ipv4 "$ip"; then
        error ping.invalid_ip "$ip"
        return 1
    fi
    # -c 4: send four packets; -W 2: wait up to 2 seconds for each reply.
    if ping -c 4 -W 2 "$ip"; then
        echo
        t ping.reachable "$ip"
    else
        echo
        t ping.unreachable "$ip"
        return 1
    fi
}

connectivity_test "$1"
