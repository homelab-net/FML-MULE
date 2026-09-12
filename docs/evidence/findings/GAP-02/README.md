# GAP-02 evidence

Enforce the service catalog: a machine-readable catalog (`services/catalog/`)
records the services a node may run, and a mission package that enables a
service with no catalog entry is refused. FML-ADR-078.

State: IMPLEMENTED. Owner: Claude. Independently verified; closure is gated on
its dependency OSS-01 (the prior-art register), which is still BASELINED. GAP-02
closes when OSS-01 does.

| Artifact | What it records |
| --- | --- |
| `implementation.md` | The catalog, the enforcement, the failing-first demonstration, and how to reproduce it. |
