# Service topology

One hosted service is checked here: the OpenTAKServer capability. The
framework can take another case later. This directory does not invent one.

Three layers, and they are not the same claim:

1. **Static composition** (`validate.py`, `manifest.yml`). The catalog root
   is `opentakserver.target`. Members require the database, the broker, and
   the mesh gate. The target waits for the members. An `After=` on the
   target alone is rejected, because units it `Wants=` would not wait with
   it. Mutations that use loopback, drop the network, publish `8088`, or
   drop the listener's database dependency must fail.
2. **Quadlet generation** (`quadlet-dry-run.sh`). The generator has to
   accept the container and network files and emit their service names.
   `Image=TBD` is replaced only in that temporary copy.
3. **Software path** (`cases/tak/integrate.sh`). Build the image, start
   PostgreSQL, RabbitMQ, and the three OpenTAKServer processes on an
   internal network, and persist one synthetic PyTAK position. The runner
   invokes podman through sudo. That is not the field pattern.

The mesh interface name is still `TBD` (`TBR-LINUX-01`). The gate unit is
unresolved on purpose. The software path does not install it and does not
claim the mesh is up. It also does not restart the stack or restore it
onto another node.

Media is out of this topology. Upstream installs ffmpeg for MediaMTX. This
image does not, and the units set `OTS_MEDIAMTX_ENABLE=false`.

CI is `.github/workflows/topology.yml`. A green static run does not start
a container. A green software path is still not hardware.
