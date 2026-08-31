# What the shared credentials do across MULEs and EUDs

**Trade:** `TBR-TAK-01`, and it bears on `TBR-NET-01`, `TBR-HA-01` and
`FML-ADR-034`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Two independent `OpenTAKServer`
instances in containers, standing in for two MULEs.

## The question

Does the shared password and user create issues for multiple MULEs on one mesh,
or for several EUDs behind one MULE? Both, in opposite directions, and both are
measured here.

There are two distinct shared credentials and this artifact keeps them apart:

- The **mesh credential** (`FML-ADR-061`, `key_mgmt=SAE`), shared by the MULEs
  of one deployment so they merge automatically.
- The **TAK credentials**: the default `administrator` / `password` account and
  the per-node certificate authority.

This is about the second.

## Two MULEs on one mesh: the same admin, and no shared trust

Two OpenTAKServer instances were run, each with its own database, data folder
and port, which is what two MULEs are: `FML-ADR-021` puts one TAK service per
node.

**Every MULE ships the same administrator credential.** Both accepted
`administrator` / `password`:

```text
MULE-A /api/login -> code 200
MULE-B /api/login -> code 200
```

The default is a constant in upstream source, so it is identical on every node
built from the same image. Capturing one MULE yields the administrator
credential for all of them.

**But no trust is shared.** Each node generates its own certificate authority:

```text
MULE-A CA fingerprint  F7:8C:72:75:9B:4C:D7:41:71:BC:40:81...
MULE-B CA fingerprint  58:73:21:57:F3:D9:DB:82:C9:63:F5:6E...
```

An EUD certificate enrolled on MULE-A **fails against MULE-B**:

```text
A's EUD cert vs A's CA:  OK
A's EUD cert vs B's CA:  error 20 (unable to get local issuer certificate)
```

Presented to MULE-B's Mission API, it returns nothing.

### The result is the worst of both

- **The thing that should be per-node is shared:** the administrator password.
  One capture compromises the fleet's TAK administration.
- **The thing that should be shared is per-node:** trust. Two MULEs on one mesh,
  in one deployment, do not trust each other's certificates. An EUD enrolled on
  its home MULE cannot authenticate to the MULE next to it.

`FML-ADR-061` makes the MULEs of a deployment **merge into one mesh
automatically**. So an EUD whose MULE fails, or who moves, is on a network full
of MULEs it can reach at layer 2 and cannot authenticate to. This is exactly the
failover case `TBR-HA-01` and `FML-ADR-034` are about, and the certificate
authority being per-node is the same finding as
`2026-08-31-different-node-restore.md` from the other direction: a replacement
that generates its own CA is not the same authority, and here neither is a
neighbour.

**A shared trust anchor across a deployment's MULEs is not present and is not
trivial to add.** It means distributing one CA, or one intermediate, to every
node, which is credential distribution with the same absence
`docs/evidence/TBR-SEC-01/2026-08-31-two-credentials-have-no-origin.md` records:
nothing in this program issues or distributes one.

## Several EUDs behind one MULE: they are not distinguishable

Two EUDs enrolled on one MULE, both with the same Common Name, `teammate`:

```text
EUD-1 enroll (CN=teammate) -> HTTP 200
EUD-2 enroll (CN=teammate) -> HTTP 200

certificates table:
  teammate  username=(null)  callsign=(null)
  teammate  username=(null)  callsign=(null)
```

**Both were issued and the two are indistinguishable.** The certificate carries
no per-device identity the server records, `username` and `callsign` are null,
and nothing rejects a second certificate with a CN already in use.

Combined with the chain in `2026-08-31-certificate-enrollment.md`, where the CN
becomes the acting user on the Mission API, this means several EUDs behind one
MULE **cannot be told apart by their certificates**, and any of them can enrol a
certificate naming any user. CONOPS section 6 plans four to eight EUDs per MULE,
so this is the normal case rather than an edge.

`THREAT_MODEL.md` already states there is no meaningful compartmentation between
admitted participants, which is deliberate for peer visibility. This is a
sharper point than that: it is not only that admitted EUDs see each other, it is
that the server cannot attribute an action to one of them, because the
credential that would attribute it is unbound and non-unique.

## What this does not establish

**The SSL streaming port was not tested.** A real ATAK client connects over TLS
with mutual authentication, which does prove possession and binds the connection
to a specific certificate. The per-node CA problem applies to it regardless --
different CA, no trust -- but the indistinguishability finding is about what the
database records, and a real client flow may populate `callsign` where this one
left it null.

**No fix is proposed.** A deployment-wide TAK trust anchor, whether EUD
certificates should carry a unique identity, and whether the administrator
password must differ per node are `FML-ADR-038`, `TBR-ID-01`, `TBR-HA-01` and
`services/ingress/` questions. This reports what the selected software does by
default across the topology CONOPS describes.

**One deployment's two MULEs, not a partition or a real roam.** The EUD did not
move; its certificate was carried between nodes by hand to test trust. What a
client does when its home node disappears was not exercised.
