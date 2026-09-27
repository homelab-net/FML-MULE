# Node descriptor fixtures

Synthetic node descriptors for exercising `tools/gen-config.py` target-awareness
(`FML-ADR-075`). Not deployable nodes; they exist only to drive the tests.

| Directory | What it exercises |
| --- | --- |
| `ap-only/node.yml` | An access-point-only active set (`wifi_ap`). Resolution is scoped to it, so non-AP bearers may stay `TBD`. No interface map, so the partial hostapd render fails closed and the oneshot refuses (`FML-ADR-083`). |
| `ap-wired/node.yml` | The same active set with concrete interface names, so the partial hostapd render reaches its success path rather than the fail-closed skip. |
