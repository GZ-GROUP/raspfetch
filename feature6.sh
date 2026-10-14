#!/usr/bin/env bash
# 6. CPU temperature in degrees Celsius.
# shellcheck source=common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

cpu_temperature() {
    local temp="" level
    # First try the Raspberry Pi tool (it prints: temp=48.3'C).
    if command -v vcgencmd > /dev/null 2>&1; then
        temp=$(vcgencmd measure_temp 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)?')
    fi
    # Otherwise read the kernel sensor (in thousandths of a degree).
    if [[ -z $temp && -r /sys/class/thermal/thermal_zone0/temp ]]; then
        temp=$(LC_ALL=C awk '{printf "%.1f", $1 / 1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
    fi
    if [[ -z $temp ]]; then
        t temp.unavailable
        emit_gauge temp none
        return 0
    fi
    # Bash cannot compare decimals, so awk classifies the temperature.
    level=$(LC_ALL=C awk -v value="$temp" 'BEGIN {
        if (value < 60) print "normal"
        else if (value < 80) print "high"
        else print "critical"
    }')
    t temp.value "$temp"
    t temp.status "$(t "temp.$level")"
    emit_gauge temp "$temp"
}

cpu_temperature
