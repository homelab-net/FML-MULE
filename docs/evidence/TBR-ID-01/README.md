# Evidence for TBR-ID-01

**Trade:** Browser-service identity provider

**Trade file:** `docs/trades/TBR-ID-01-browser-service-identity-provider.md`

**Priority:** 14 of 16 (SAD v0.31 section 30.2). **Function owner:** Security/Identity.
**Named owner:** Cameron Zobrist.

**Current contents:** two artifacts. This trade remains `OPEN`; an artifact's
presence is not owner acceptance, and nothing here is a selection.

- [2026-10-17-authentication-events-with-and-without-a-common-idp.md][artifact-1]
- [2026-10-17-offline-client-certificate-login-fakes.md][artifact-2]

[artifact-1]: 2026-10-17-authentication-events-with-and-without-a-common-idp.md
[artifact-2]: 2026-10-17-offline-client-certificate-login-fakes.md

The first is written analysis: authentication events counted with and without
a common identity provider, for the two-entry catalog the program fields and for
the nine CONOPS section 49 classes, plus the provisioning burden per user per
mission and the behaviour when time is not credible. For the fielded catalog it
finds no provider is required. For the planning case it recommends, without
selecting, ingress client-certificate authentication over a provider service,
and names the phone measurement that should come first.

The second is `SIMULATED`: that option demonstrated offline against fakes, in
a namespace holding only loopback, 20 of 20 cases on each of 22 runs across an
x86-64 desktop and `pi-mule-1`.

Still owed for closure: the owner's decision, an ADR recording it, and offline
login demonstrated for whatever is selected. The analysis's finding 6 also
records that three documents cite this trade for enrollment and API-path
questions its closure gate does not cover.

This directory existed before the work did, deliberately. The closure gate is
written in the trade file before evidence is gathered, so the result cannot be
graded against a standard invented after seeing it.

## What belongs here

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are transcribed from the SAD and are authoritative;
this file does not restate them, so that the two cannot drift apart.

Every artifact follows the naming and recording rules in
`docs/evidence/README.md`:

- `YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`
- Measurements record instrument, date, node, image build, configuration,
  ambient conditions, and who took them.
- Vendor datasheets go in `datasheets/` with a `.SOURCE.md` recording the
  URL, retrieval date, and document revision. Archive them when you cite them;
  vendors delete PDFs. SAD section 34 is the program's external source register.
- Nothing real: no deployment location, member identity, callsign, credential,
  or operational capture. Strip photograph metadata. See `SECURITY.md`.

**Requires hardware:** No. Workflow analysis and offline login can be exercised against fakes on an

## Closing

Evidence here is necessary and not sufficient. SAD section 30.2: a TBR closes
only when its listed evidence exists, **the named owner accepts the evidence**,
and the resulting architecture decision is entered into the persistent ADR
register.

Closing a trade whose named owner is still `TBD-SRR` is not possible, because
there is nobody to accept the evidence. This trade's owner was named on
2026-10-02, so that bar is cleared; it says nothing about whether the evidence
below meets the gate.
