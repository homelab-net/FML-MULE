#!/bin/bash
# Sample the TAK server's established client sessions, for the partition trial.
#
#   tak-session-sample.sh SECONDS OUT.jsonl [PORT]
#
# Every 2 s, one JSON line: the UTC time and, for each established session on
# PORT (8089), the client address:port and its send queue. The analysis reads how long the
# server keeps a partitioned client's session open after the client has gone,
# which decides whether the server still routes to a client it cannot reach.
# Needs no root.
set -eu
SECONDS_TO_RUN="${1:?seconds}"
OUT="${2:?out file}"
PORT="${3:-8089}"
end=$(($(date +%s) + SECONDS_TO_RUN))
while [ "$(date +%s)" -lt "$end" ]; do
  peers=$(ss -Htn state established "( sport = :$PORT )" |
    awk '{printf "%s{\"peer\": \"%s\", \"sendq\": %s}", (NR > 1 ? ", " : ""), $4, $2}')
  printf '{"t": "%s", "peers": [%s]}\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$peers" >>"$OUT"
  sleep 2
done
