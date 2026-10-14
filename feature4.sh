#!/usr/bin/env bash
# 4. Network configuration: interfaces, IP addresses and configured routes.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

network_config() {
    local gateway
    t network.interfaces
    ip -br address
    echo
    t network.routes
    ip route
    gateway=$(ip route | awk '/^default/ {print $3; exit}')
    echo
    t network.gateway "${gateway:-$(t network.none)}"
}

network_config
