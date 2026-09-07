#!/bin/sh
# Report the resident memory of the mission-service plane from a running
# reference deployment -- the software half of TBR-COMP-01's "size" axis, the
# number the CM4 memory class (4 GB vs 8 GB) is chosen against.
#
# Usage: test/bench/service-plane-footprint.sh [container ...]
#   With no arguments it measures the reference deployment's container set
#   (the fml-* stack the dev host runs persistently; see docs/dev-machine.md).
#   Pass container names to measure a different running stack.
#
# WHAT THIS IS FOR. TBR-COMP-01 is CRITICAL and its dependency TBR-TAK-01 is now
# CLOSED, so its software half is bankable. SAD section 25.3 requires an explicit
# compute/memory model, and "the host hardware is not selected until the resource
# model and power model agree." The failure mode FML-ADR-021 accepted is that the
# service plane starves the routing daemon; this measures how much the service
# plane actually takes, so the network-plane reserve is set against a number
# rather than a guess. The tile server was sized on its own on 2026-09-06
# (test/bench/map-server-footprint.sh); this sizes the rest of the stack.
#
# WHY IT MEASURES A RUNNING DEPLOYMENT, NOT A STAND-UP. A representative footprint
# needs a *working, warmed* OpenTAKServer, and standing OTS up from scratch has
# several stacked requirements: it needs PostGIS (not plain PostgreSQL), a
# data folder its non-root user can write, a Python < 3.13 base (its gevent WSGI
# server asserts this -- on python:3.13 the API never binds), and a staged start
# so the three OTS processes share an initialised data folder. The dev host
# already runs exactly this as a persistent bench, warmed over days; reading its
# resident memory is read-only and safe, and it is a real deployment rather than
# a synthetic one. A self-contained stand-up is a worthwhile follow-up but is not
# required to bank the number.
#
# WHAT OTS IS. Three long-running processes, which this makes visible: the API
# (opentakserver), the CoT streaming handler (eud_handler), and the parse/persist
# worker (cot_parser) -- the third that tak-state.sh notes upstream's single-entry
# Dockerfile omits. RabbitMQ is its broker; PostGIS is its store (FML-ADR-034);
# nginx fronts it (FML-ADR-031 ingress).
#
# WHAT IT DOES NOT DO, and it is deliberately not the whole budget.
#   - It is the x86 dev host, NOT the CM4. RSS is a size estimate; the arm64
#     figure and CPU-under-load on the CM4 are TBR-COMP-01's hardware item and
#     stay open. It selects no host.
#   - It is the "size" half at steady state only. The reservation mechanism
#     (systemd limits, a reserved core, priority -- SAD 10.4), OOM under
#     contention, swap policy, "holds mesh links through a service-plane peak",
#     and a peak under a client association storm all need the network plane
#     co-resident and the storm needs radios. None is here; tier SIMULATED.
#   - PostgreSQL/PostGIS reports low resident memory at idle because shared
#     buffers are allocated lazily; under query load its footprint grows toward
#     shared_buffers. The steady-state figure is a floor for the DB, not a peak.
#   - It reads memory only; it injects no load, so as not to disturb a live
#     deployment. No credential or real data is read or written.

set -eu

# The reference deployment's container set, in shed order (front to back).
DEFAULT_SET="fml-ots fml-eud_handler fml-cot_parser fml-mq fml-pg fml-nginx-tls fml-nginx-api fml-tiles"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

command -v podman >/dev/null 2>&1 || fail "podman is not installed."

if [ "$#" -gt 0 ]; then
  SET="$*"
else
  SET="$DEFAULT_SET"
fi

# Confirm the stack is running before reading it.
for c in $SET; do
  podman container exists "$c" 2>/dev/null || fail "container '$c' is not present. Start the reference deployment (docs/dev-machine.md), or pass container names."
  state=$(podman inspect "$c" --format '{{.State.Running}}' 2>/dev/null || echo false)
  [ "$state" = true ] || fail "container '$c' is not running."
done

printf '=== Service-plane footprint (steady state, x86 reference deployment) ===\n'
printf '  tier: SIMULATED -- size half only; no network plane co-resident; no load\n\n'

# podman stats MemUsage is the container cgroup's current memory. Sum it in MB.
# shellcheck disable=SC2086
podman stats --no-stream --format '{{.Name}}|{{.MemUsage}}|{{.CPU}}' $SET 2>/dev/null |
  awk -F'|' '
    {
      v = $2; sub(/ *\/.*/, "", v); g = (v ~ /GiB/)
      sub(/[MG]iB.*/, "", v); if (g) v = v * 1024
      cpu = $3 + 0
      printf "  %-18s %8.1f MB   (CPU %.2f%%)\n", $1, v, cpu
      tot += v
    }
    END { printf "\n  %-18s %8.1f MB\n", "AGGREGATE", tot }'

printf '\n  This is the steady-state "size" input for TBR-COMP-01. The CM4/arm64\n'
printf '  footprint, CPU under load, and the peak under a client association storm\n'
printf '  remain and need hardware and the network plane.\n'
