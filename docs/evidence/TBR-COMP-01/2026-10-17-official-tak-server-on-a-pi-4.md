# The official TAK Server on a Raspberry Pi 4: footprint, start-up and a soak

**Tier: deferred (real-hardware bench result; formal `HARDWARE-VERIFIED` held).**
Held for the reasons `docs/evidence/TBR-RF-01/2026-10-11-two-node-80211s-batman-real-radio.md`
gives, unchanged. Target-class arm64 hardware, measured on the node itself.

**Trade:** `TBR-COMP-01`, and CONOPS section 31. It evaluates `FML-ADR-032`'s
fallback, *"Another TAK-compatible server"*; it does not change the preferred
server, which remains OpenTAKServer.
**Date:** 2026-10-17 16:45 to 2026-10-18 00:10 MDT. **Taken by:** Cameron
Zobrist, on the mule bench, with Claude.
**Nodes:** `pi-mule-1` and `pi-mule-2`, Raspberry Pi 4B, 8 GB, Debian 13
(trixie) arm64, `6.18.50+rpt-rpi-v8`. **Software:** TAK Server
`5.8-RELEASE92` (the `takserver_5.8-RELEASE92_all.deb` from tak.gov, sha256
`369a7910a16949e802087e653ed580ac1eafc818c666dcb6aa9576da94867408`), Temurin
`17.0.20.1`, PostgreSQL `18.6` with PostGIS `3.6.4`, installed by
`test/bench/tak-server-bench-install.sh`. **Clients:** WinTAK `5.8.0.147`
(Windows 11) and `test/bench/tak-sim.py`. **Power:** every one of 125
one-minute samples during the soak read `throttled=0x50005`, under-voltage
and throttled now; the CPU sat at 600 MHz against a nominal 1.8 GHz.

## Why this exists

`TBR-COMP-01` has one size figure: the OpenTAKServer service plane at about
650 MB resident, measured on x86 and labelled `SIMULATED`
(`2026-09-06-service-plane-steady-state-footprint.md`). The program needs a
target-class figure, and `FML-ADR-032` names another TAK-compatible server as
its fallback. This is that fallback, on the hardware class the program builds
on.

## What this does not establish

- **Not the selected plane's size.** OpenTAKServer was not measured on the Pi
  here. The two figures are different servers on different architectures and
  are not a head-to-head.
- **Not CPU.** The node was throttled throughout, so no CPU figure is reported
  and start-up times are upper bounds for this hardware.
- **Not load.** At most six client sessions and about one report per second in
  aggregate. No association storm, no peak.
- **Not a leak test.** These JVMs size their heaps at start-up, some with
  `-XX:+AlwaysPreTouch`, so flat resident memory cannot show a leak inside the
  heap.
- **Not licence-cleared for images.** The package came from tak.gov under its
  terms and is not committed. Whether those terms permit shipping it in a
  published MULE image was not examined, and has to be before anyone proposes
  it as a baseline.

## Installing on Debian 13

The package `Depends: openjdk-17-jdk, postgresql-18, postgresql-18-postgis-3`.
Debian 13 carries OpenJDK 21 but not 17, and PostgreSQL 17 but not 18. The
installer adds the vendors' own repositories (Adoptium, PGDG), both of which
publish arm64 builds for trixie, and satisfies `openjdk-17-jdk` with a local
`equivs` package that depends on `temurin-17-jdk`, so apt stays consistent
rather than being forced past a dependency.

Two defects in the first install script stopped the server, and both are fixed
in the committed one:

- **The config service could not read `CoreConfig.xml`.** A `umask 077` set to
  protect a generated secrets file stayed in force, so the file was created
  `root` `0600` and the `tak` service user could not read it. The config service
  failed with a `NullPointerException`, and messaging and the API then failed
  because they read their configuration from it.
- **The database rejected the configured password.** The package's own
  post-install creates the database role; the setup script, run again with a
  password, leaves an existing role's password unchanged. The role is now
  aligned explicitly.

## Results

### Resident memory

| Node, state | Java, all JVMs | PostgreSQL | Available of 7,819 MB |
| --- | --- | --- | --- |
| `pi-mule-1`, idle, about ten minutes after start, one client | ~3,180 MB | ~490 MB | ~4,020 MB |
| `pi-mule-1`, two-hour soak, 125 samples | **2,971 to 3,000 MB** | **473 to 511 MB** | 4,140 to 4,212 MB |
| `pi-mule-2`, about seven minutes into a restart, **not settled** | ~2,325 MB | ~461 MB | ~4,880 MB |

So **about 3.5 GB resident** with clients connected, roughly five times the
OpenTAKServer figure, subject to the caveat above. The server sizes its heaps
from total memory; on this 8 GB node it chose 1,271 MB each for the API and
messaging processes, 266 MB each for plugins and retention, and 228 MB for
configuration. How it behaves, or whether it fits, on a smaller compute element
is not measured here, and that is the question `TBR-COMP-01` actually needs
answered.

### Start-up and stop

| Event | Time to serve TLS on 8089 |
| --- | --- |
| `pi-mule-1`, start after the configuration fix | 11 min 45 s |
| `pi-mule-1`, start after the database fix | 8 min 10 s |
| `pi-mule-2`, first start | about 11 min 30 s |
| `pi-mule-2`, restart | 7 min 50 s |

Stopping it took about twelve seconds. Listening is not the same as ready:
`docs/evidence/TBR-HA-01/2026-10-17-tak-field-ingress-and-administrative-promotion.md`
records a restarted server that passed a port check and did not relay traffic
for another thirteen seconds. Under CONOPS 31, a node hosting this server pays
these minutes every time the service starts.

### Interoperability with WinTAK

WinTAK `5.8.0.147` imported a connection package made by the server's own
`make-connection-package.sh` and connected by client certificate with nothing
typed; the server logged the subscription and assigned the client's callsign.
A second client, `tak-sim.py` with another certificate from the same CA, then
exchanged traffic with it through the server:

| Direction | Observed |
| --- | --- |
| WinTAK position, to the second client | received 0.2 s after the second client connected |
| second client's position, to WinTAK | logged by WinTAK as a Team Member map marker at the placeholder 0,0 |
| second client's GeoChat, to WinTAK | written to WinTAK's chat database about **59 ms** after it was sent (same host clock) |

WinTAK sending a GeoChat needs a person and was not exercised. No phone used
this server.

### Two-hour soak

One `tak-sim.py` session held for **exactly 120 minutes without a disconnect**:
1,430 position reports at five-second intervals, the largest gap between sends
6.0 s, and 1,623 relayed events received, from WinTAK and from the probe
clients of the concurrent promotion trials. Sixteen trials ran during the soak,
six of which partitioned this server from the mesh; this session, arriving over
the LAN, was unaffected throughout. Resident memory stayed within the band in the table
above.

## What this changes

Nothing is decided. For `FML-ADR-032`'s fallback, these are the numbers a
decision would weigh: about 3.5 GB resident on an 8 GB node, start-up measured
in minutes, a stop in seconds, a two-hour session without a drop, and WinTAK
interoperability by certificate. The licence question comes first, and
OpenTAKServer on the same Pi is the comparison still owed.
