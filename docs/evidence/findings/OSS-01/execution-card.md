# OSS-01 execution card

## Finding and authority

- **Finding:** OSS-01, build the prior-art and reuse register.
- **Governing records:** the remediation plan's open-source-first policy and
  OSS-01 closure gates; `AGENTS.md` rule 6; existing ADRs and open trades named
  by each candidate evaluation.
- **Owner approval:** the project owner approved the proposed registry, schema,
  evaluation documents, validator, regression tests, and mutation tests in the
  Codex thread on 2026-09-09.
- **Architecture authority:** this work records evidence and may not adopt,
  reject, or change a component architecture without the separately required
  project-owner decision.

## Exact scope

The version 1 corpus contains these 28 candidates:

1. Project N.O.M.A.D.
2. OpenMANET firmware.
3. `openmanetd`.
4. Reticulum.
5. NomadNet.
6. Martin.
7. OpenTAKServer.
8. PyTAK.
9. Meshtastic.
10. HAProxy.
11. Podman and Quadlet.
12. `batman-adv` and `batctl`.
13. `hostapd`.
14. `wpa_supplicant`.
15. `dnsmasq`.
16. `systemd-networkd`.
17. `nftables`.
18. `chrony`.
19. OpenSSH server.
20. Smallstep `step-ca`.
21. PostgreSQL.
22. Kiwix.
23. Kolibri.
24. ProtoMaps.
25. PMTiles.
26. Tailscale client.
27. Morse Micro Linux driver.
28. Morse Micro firmware.

Transitive components are reviewed inside the candidate that bundles or
requires them unless an FML record selects them directly. ATAK and iTAK are
external EUD clients rather than shipped MULE dependencies. Development-only
lint packages remain governed by `FML-ADR-058` and the existing toolchain lock.

## Outputs

- `docs/prior-art/registry.yml` and
  `docs/prior-art/registry.schema.json`.
- One evaluation document for each candidate that reaches `EVALUATED`.
- `tools/validate-prior-art.py`, called by `tools/validate-docs.sh`.
- Focused tests that demonstrate missing candidates, floating references,
  missing evidence, incompatible reuse modes, and adoption without approval are
  rejected.
- Mutation cases proving the focused tests notice removal of the principal
  controls.
- Closure evidence under this directory after all 28 records are current.

## Versioned verification contract

“Every substantial planned component” means exactly the 28-item version 1
corpus above. Adding a directly selected runtime, build, deployment, driver, or
firmware component expands the corpus in the same change that proposes it.

An item is current when its evaluation date is no more than 90 days before the
verification date and its immutable evaluated artifact still resolves from the
canonical upstream. The 90-day period is a review budget for this register, not
a product requirement.

An evaluated record contains every field in the remediation plan's OSS intake
record. Resource values may be `not-measured`, but no number may be invented.
An `adopt`, `wrap`, or `port` reuse mode requires a non-placeholder owner
approval reference. `pattern-only`, `reject`, and `undecided` are assessments,
not architecture decisions.

The focused fixture corpus contains one valid baseline registry and at least
these 11 invalid cases:

1. A required candidate is missing.
2. A candidate identifier is duplicated.
3. An evaluated Git or OCI artifact lacks an immutable identifier or carries
   an impossible verification date.
4. An evaluation document is missing or escapes `docs/prior-art/`.
5. A document exists but is absent from the registry.
6. A license-incompatible candidate requests a reusable mode.
7. An architecture-changing reuse mode has no owner approval.
8. An evaluated claim section has no substantive evidence source.
9. An evaluated candidate has no exact FML-MULE requirement mapping.
10. A mapped requirement or remediation finding does not resolve.
11. A required narrative field contains only whitespace.

The full gate is `tools/lint.sh`. Closure also requires a new clean checkout,
empty caches, all 28 records evaluated, all retained references re-resolved,
secret scanning, and independent P0 review.

## Red-team plan

- Replace an immutable commit or digest with `main`, `latest`, or a tag alone.
- Remove a required candidate and duplicate another identifier.
- Point an evaluation outside the prior-art directory or delete its file.
- Mark a license-incompatible project for adoption.
- Mark a candidate `adopt`, `wrap`, or `port` without owner approval.
- Change an upstream license or bundled dependency result in a disposable
  fixture.
- Exercise documented prototype commands without privileged or production
  state and record any root, socket, network, or persistence requirement.

Every planted fault stays in a disposable fixture and shall be absent from the
final diff.

## Rollback and completion

The increment is reverted by reverting its commits; it changes no product
runtime or lab device. OSS-01 closes only when all plan closure gates and the
verification contract above pass, its evidence is independently reproduced,
and the project owner has approved every reuse mode that changes architecture
or licensing posture.
