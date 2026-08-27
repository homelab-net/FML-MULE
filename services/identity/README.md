# Identity

PKI, node admission, and the handling of mission trust material.

**Nothing is implemented. No key material of any kind is in this repository,
and none ever will be.**

## The publication rule, stated where it matters most

**No private key, certificate, credential, mission package with real
identities, or captured operational data ever enters this repository.** Not in
code, not in documentation, not in an example, not in a test fixture, not in a
screenshot, not in a log excerpt pasted into an issue.

`.gitignore` covers `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.jks`, `.env`,
`secrets/` and `mission/local/`, and secret scanning runs in CI. Both are
backstops. The control is the person committing.

If key material reaches `main`, treat it as compromised and rotate it. Removing
the commit does not undo publication.

## Design intent, all UNVERIFIED

Selected components: **Smallstep `step-ca`** as the preferred initial PKI
(`FML-ADR-036`), the **Mission Trust Service** for signed state distribution
(`FML-ADR-047`), the **hostapd integrated EAP server** for offline EAP-TLS
admission (`FML-ADR-038`, with FreeRADIUS as an approved alternate), and
**application-native RBAC first** with OPA only where cross-application policy
justifies it (`FML-ADR-037`).

Recorded so a reader knows what the program is aiming at, and knows that none
of it is demonstrated:

- **Node identity** rests on a program PKI. Each node holds a credential
  identifying it as a member of the program.
- **Mission admission** sits above node identity: being a valid node does not
  admit you to a particular mission. The mission trust layer decides that, and
  it is a placeholder component that must not be implemented yet; see
  `services/mission-trust/`.
- **Trust validation never fails open on invalid time.** A node that cannot
  establish credible time refuses to validate credentials rather than accepting
  material it cannot check, and reports that its time is not credible so an
  operator can see why. `FML-ADR-042`, `TBR-TIME-01`.
- **Protected storage** limits what a captured node discloses. Its strength
  depends entirely on how the volume is unlocked, which is unsolved:
  `TBR-SEC-01`.

## What is genuinely hard here

Three problems, none of which has a clean answer, all recorded so that nobody
believes they are details:

**Unattended unlock.** A field node boots with no operator, no network, and no
reachback. Every purely local answer reduces to keeping the key on the device.
`TBR-SEC-01`. Until it closes, at-rest encryption protects against a casual
finder and not against a motivated one, and `THREAT_MODEL.md` says exactly
that.

**Revocation in a disconnected network.** A credential revoked centrally is
still valid on a partition that has not learned of the revocation. Assume a
revoked credential remains usable there. How long that window is, and whether
it can be bounded at all, is `TBD`.

**Capture is a mission-wide credential compromise.** A captured node holds
material that admits it to the operational domain. Physical capture is an
expected condition, not an edge case. The recovery procedure for a lost node,
including rotation, is `TBD` and belongs in the CONOPS as a procedure rather
than here as a feature.

## Fail closed

Where identity or trust cannot be established, the system refuses rather than
proceeds. That is a decided property (`FML-ADR-042`), and it will be unwelcome
the first time a node with a dead clock battery refuses to join during an
incident. The operator-visible reporting requirement exists so that it is
diagnosable rather than mysterious.

Failing open would make the credential system decorative, which is worse than
having none, because a decorative control gets relied on.
