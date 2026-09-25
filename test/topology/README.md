# Service topology

One hosted service is checked here: the OpenTAKServer capability. The
framework can take another case later. This directory does not invent one.

Three layers, and they are not the same claim:

1. **Static composition** (`validate.py`, `manifest.yml`). The catalog root
   is `opentakserver.target`. Members require the database, the broker, and
   the mesh gate. The target requires the workers and infrastructure but only
   wants the API; worker `ExecStartPre=` checks make API startup fail closed
   without coupling later API loss to their lifetime. An `After=` on the
   target alone is rejected, because units it `Wants=` would not wait with
   it. Mutations that use loopback, drop the network, publish `8088`, drop
   the listener's database dependency, or remove its API-start gate must fail.
2. **Quadlet generation** (`quadlet-dry-run.sh`). The generator has to
   accept the container and network files and emit their service names,
   including `--sdnotify=healthy`. `Image=TBD` is replaced only in that
   temporary copy.
3. **Cold start** (`cases/tak/cold-start.sh`). An unprivileged account with a
   subordinate UID range installs the materialized units and systemd starts
   `opentakserver.target`. `Notify=healthy` is what makes `After=` wait for
   PostgreSQL, RabbitMQ, the API migrations, and the listener. The script
   does not start those containers. It first forces API startup to fail and
   requires both workers to stay closed. The normal start then persists one
   synthetic PyTAK position. Afterward the API is stopped by itself and the
   target/listener/parser must remain active. The row must also survive a
   target stop/start.
   The account is not a selected field user. The run is rootless. It is
   not host root. The topology jobs run on Ubuntu 26.04 and use Ubuntu's
   systemd-enabled Podman 5 package. A prior static Podman fallback accepted
   health-check configuration but was built without systemd support, so its
   health checks were never scheduled. Cold start now proves the rootless
   health scheduler reaches `healthy` before exercising `Notify=healthy`.

The mesh interface name is still `TBD` (`TBR-LINUX-01`). The gate unit is
unresolved on purpose. Cold start installs a user unit of the same name
and holds it closed until the members are observed not to be running.
That is the dependency edge. It is not a mesh, and the runner has no
radios. Stopping the target and starting it again keeps the row. That
does not set `Restart=` and does not restore the durable set onto
another node.

Media is out of this topology. Upstream installs ffmpeg for MediaMTX. This
image does not, and the units set `OTS_MEDIAMTX_ENABLE=false`.

CI is `.github/workflows/topology.yml`. A green static run does not start
a container. A green cold start is still not hardware.
