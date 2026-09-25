# Native runtime unit

This directory contains the native host unit selected by `FML-ADR-083`. The
unit invokes the bounded `python -m mule` configuration renderer and exits; it
is not a mission-service container or a long-running service controller.

`mule-runtime.service` is intentionally static. It has no `[Install]` section,
so the base image does not start it before deployment-specific inputs exist.
Provisioning supplies `/etc/fml/region.yml`, `mission.json`, `node.yml`, and the
approved service catalog, then starts the unit explicitly. Failure is visible
as a failed invocation. `Restart=` and `OnFailure=` remain absent while
`TBR-HA-01` is open.

The renderer runs as a transient unprivileged user and writes only its private
`/run/fml` directory. A later configuration applier, if one is required, needs
its own authority decision; render access is not silent permission to mutate
host networking.
