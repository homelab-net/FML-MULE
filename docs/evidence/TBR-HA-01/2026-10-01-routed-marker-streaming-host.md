# Routed marker delivery and controlled streaming-worker movement

## Question and scope

Can a synthetic shared marker travel from prototype node-b through node-a to
the bench TAK server and open in iTAK? Can the streaming worker move to node-a
while the phone retains its existing server configuration?

This confronts the service and Linux integration uncertainty under
`FML-ADR-031`, `FML-ADR-071`, `FML-ADR-086`, `TBR-LINUX-01` and `TBR-HA-01`.
It is a manual prototype observation, not an automatic recovery mechanism or
trade closure. The existing assigned bench remains the EUD ingress and the
authoritative SQL/broker host throughout the worker movement.

## Provenance and deviations

The desktop agent ran the trial under the Program Owner's instruction on
2026-10-01. Host/source/image identities are recorded in the
[earlier node provenance][provenance]. Instruments are Linux `ip`, `ping`,
`nft`, `ss`, PyTAK, OpenTAKServer 1.7.13, PostgreSQL queries, OpenSSL and the
operator's iTAK screenshots. Screenshots remain private; they contain phone
context that is unsuitable for publication. Selected synthetic-only command
outputs are in the [sanitized raw record][raw], with original and sanitized
hashes in the [metadata][metadata]. No calibrated recovery-time measurement
was made. Ambient, antenna and regulatory conditions were not recorded.

The radio bearer is the existing infrastructure AP-dependent BATMAN_IV trial,
with its recorded deviations from selected 802.11s and network ownership.
Temporary IPv4 host routes force node-b to reach the bench via node-a, with a
matching return host route. This is actual node-a IP forwarding over that
bearer; it is not independent RF multihop or an 802.11s demonstration.
Node-a's trial forwarding filter admits only this pair's ICMP and TAK TCP
traffic. Management remains independent. Redirects are disabled for the trial
to prevent same-interface forwarding from teaching a bypass route. Original
per-interface sysctl values are saved for restoration.

## Connection failure and marker usability

The phone's existing TLS connection failed while the bench had a plaintext
TAK listener but no SSL listener. Its SSL worker had been started as a detached
exec child of the plaintext worker container. The live startup script explicitly
warned that restarting the container discards that SSL process.

The older nginx TLS terminator was deliberately retired in that script. It was
briefly started during diagnosis, then stopped when the live configuration was
read. Native OpenTAKServer SSL was restored. The phone reconnected over the
existing assigned Tailscale ingress; no re-enrollment or grant change was made.

The operator received notifications for the earlier short-lived position
events, but opening them reported that the related object could not be found.
SQL confirmed those events were expired. A fresh standard spot-map marker
(`b-m-p-s-m`), with a test-configured one-hour expiry and deliberately synthetic
nonzero coordinates, opened successfully in iTAK. The operator screenshot shows
its marker label, coordinates and baseline remarks. Both format and lifetime
changed, so this does not isolate expiry as the sole cause of the older error.

The spot-map structure follows the upstream [TAKPacket SDK marker example][spot].
It uses the standard contact, archive, color, usericon and remarks fields;
no private TAK extension or payload is introduced.

## Forced transit and negative control

The single bench-origin spot marker was tested first. Node-b then reached the
bench via node-a: three ping replies had TTL 63, and the TAK socket connected.
Node-a forwarding counters recorded the two directions. Inserting a drop at
the beginning of the trial forwarding chain produced two lost pings and a TAK
socket timeout. Node-b's Ethernet/router control ping still passed. Removing
the drop restored reachability.

Node-b sent a fresh spot marker through that route. The bench stored its
synthetic UID and node-a's TCP counters increased. The operator opened that
specific marker in iTAK and the screenshot shows its `forwarded-baseline`
remarks. This confirms receipt and usable rendering beyond SQL arrival or a
notification. Those temporary routes, filter and sysctl changes were restored
before the next trial, then installed again for the moved-worker send.

## Controlled streaming-worker movement

The independent `qualify_lora_boot` agent identified a source-supported route:
retain the assigned bench ingress, use opaque TCP passthrough to node-a's
native SSL worker, and keep that worker on the existing authoritative SQL and
RabbitMQ state. The separate Pi prototype databases are not promoted.

Node-a generated its own server private key. The existing bench CA signed its
CSR with a certificate valid for the unchanged logical service identity. The
CA key and the bench server key stayed on bench. OpenSSL verified the new
leaf's chain and hostname. A separate temporary worker data directory prevents
the Pi's ordinary configuration from overriding the trial dependencies.

SQL and broker traffic use encrypted SSH tunnels coordinated by the desktop;
the Pi forwarding listeners bind only loopback. The first coordinator version
misrouted broker traffic to SQL because Paramiko stores one forwarding callback
per transport. Corrected dispatch uses the forwarded destination port. SQL and
broker preflight then both passed before live traffic was switched.

The bench native SSL processes were stopped and a temporary nginx stream proxy
listened at the same ingress endpoint, forwarding opaque TLS to node-a. This
reuses an installed image rather than installing HAProxy for one test; it is a
bench deviation from the preferred proxy in `FML-ADR-031`. The phone reconnected
with an established bench-to-node-a SSL socket and an active node-a broker
connection. No handler warning or error was recorded in the bounded sample.

Node-b sent an updated value on the same synthetic marker UID through node-a's
forced route. SQL records the later `node-a-streaming-host` phase. Operator
confirmation that the updated phase is visible in iTAK is pending; the connected
socket and stored update alone do not establish usable EUD delivery after the
worker movement.

A repeat switched the worker again and sent a distinct synthetic marker UID
to avoid cached-object ambiguity. The bench native SSL container was stopped;
the selected proxy, node-a SSL socket, forced transit counters and matching SQL
row were recorded. The phone's configuration was not changed by orchestration.
Operator confirmation that this new marker opens is also pending. The stable
bench service was restored before ending the run.

OpenTAKServer's [native SSL implementation][ssl] reads the backend leaf/key and
client trust from its CA directory. Its [handler implementation][handler] maps
the client certificate subject to an active SQL user and uses SQL membership
and RabbitMQ for recipient routing. The trial preserves those dependencies.

## Limits and restoration

This moves the TLS/authentication and streaming worker only. The bench remains
the assigned WAN ingress, authority and durable-state host. The desktop remains
in the dependency tunnel path. It does not demonstrate losing either host,
database replication, writer promotion, fencing, state reconciliation,
autonomous failover or compliance with a recovery-time objective. No TBR closes.

The connection-loss defect is addressed on the bench by running native SSL
as a separate persistent container and adding it to existing startup/stop
paths. Restarting the plaintext worker retained the same SSL process and
listener. Restarting the SSL container restored its own listener. The startup
script passes shell syntax checking and the modified systemd unit passes
`systemd-analyze verify`. The existing startup path was executed successfully.
Whole-host reboot recovery was not exercised in this trial.

Bench native SSL service was restored. Temporary routes, forwarding filter and
per-interface sysctl values were restored and checked; temporary proxy and Pi
worker were removed, SSH forwards closed, and temporary dependency credentials
removed from the Pi. The AP-dependent BATMAN trial remained available at the
end of this capture. The [subsequent power follow-up][power-followup] records
the later reboots, loss of that temporary overlay, and DNS/sleep repairs. This
rootful bench arrangement does not change
the production rootless catalog or decide the open recovery trade.

[provenance]: ../TBR-LINUX-01/2026-10-01-infrastructure-wifi-prototype.json
[raw]: 2026-10-01-routed-marker-streaming-host.txt
[metadata]: 2026-10-01-routed-marker-streaming-host.json
[spot]: https://github.com/meshtastic/TAKPacket-SDK#marker--spot-map-b-m-p-s-m
[ssl]: https://raw.githubusercontent.com/brian7704/OpenTAKServer/1.7.13/opentakserver/eud_handler/EudServerSSL.py
[handler]: https://raw.githubusercontent.com/brian7704/OpenTAKServer/1.7.13/opentakserver/eud_handler/EudHandler.py
[power-followup]: ../TBR-LINUX-01/2026-10-01-power-ble-followup-node-a.md
