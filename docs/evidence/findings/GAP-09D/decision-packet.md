# GAP-09D decision packet: MULE runtime packaging

**State:** `APPROVED`; implementation remains open. The Program Owner approved
the recommended entry point, installation model and unit shape on 2026-09-25.
`FML-ADR-083` records the controlling decision. No `Restart=` or `OnFailure=`
policy is selected here because `TBR-HA-01` remains open.

**Finding:** GAP-09D. **Prepared:** 2026-09-21. **Author:** Claude agent
(redirected from Codex). **Independent verifier:** a separate agent at execution
time.

## 1. Decision requested

Three linked questions, currently reserved by the codebase itself:

1. The **entry-point form** for the `mule` runtime.
2. The **installation and versioning model** -- how `mule` reaches the image and
   is versioned against the `FML-ADR-040` compatibility set.
3. The **systemd unit shape** that supervises it.

`mule/__init__.py` states plainly: "There is no service daemon and no process
entry point here, and there will not be one until an implementation ADR decides
how this package is installed onto an image and versioned against the
compatibility set in `FML-ADR-040`." So this is a genuine open architectural
decision, not a mechanical packaging step.

## 2. Governing constraints

- `FML-ADR-051`: `mule/` holds the decisions a node acts on while running (one
  module per question); production standards.
- `FML-ADR-040`: the field kernel/radio-driver set is a gated, pinned
  compatibility set -- `mule`'s versioning must bind to it.
- `FML-ADR-029`: the **service plane** runs as rootless Podman Quadlets; the
  `mule` node runtime is host decision logic, so its execution form (native
  systemd service vs otherwise) is part of this decision, not assumed.
- **Open trades that must not be prejudged:** `TBR-HA-01` (restart/recovery
  policy) and `TBR-LINUX-01` (interface-bound unit naming). `os/config/systemd-units.template`
  is bound to both.

## 3. Options (for the Owner)

**Entry-point form:**

- (a) a `console_script` exposed by making `mule` an installable distribution
  (today `pyproject.toml` is `fml-mule-tools` and explicitly "does not build a
  distributable package");
- (b) a `python -m mule` module entry (`__main__.py`), no console script;
- (c) a **oneshot config-render** entry (decide + render config, then exit),
  supervised by systemd `Type=oneshot`;
- (d) a **long-running supervisor** built on the existing loop orchestration
  (`mule/loops.py`).

**Installation / versioning model:** pip-install `mule` into the image at build
time; a Debian package; or a vendored module -- each versioned against the
`FML-ADR-040` set. This is the part that needs the new implementation ADR.

**Systemd unit shape:** `Type` (oneshot vs notify/simple), ordering
(`After=`/`Wants=` the network plane), and privilege (native host service vs a
narrowly scoped helper per SAD 9.3).

## 4. Approved disposition

The Owner selected **(c) a `Type=oneshot` config-render entry via
`python -m mule`**, installed as a Python distribution in the image and bound to
the `FML-ADR-040` compatibility set. `FML-ADR-083` records the decision and
keeps restart policy deferred to `TBR-HA-01`.

## 5. Consequences and the gates this must NOT close

- **`TBR-HA-01` (OPEN):** a unit needs restart/failure behavior. This packet
  presents `Restart=` / `OnFailure=` as an **option set deferred to `TBR-HA-01`**;
  it writes no default. A concrete restart line would silently close that trade.
- **`TBR-LINUX-01` (OPEN):** any interface-bound unit name is deferred; the
  milestone unit is named for the runtime, not a radio interface.
- **`FML-ADR-040`:** the installation model changes how the compatibility set is
  versioned -- hence a new ADR, Owner-approved, before code.
- Making `mule` a distributable package changes `pyproject.toml`'s current stance
  -- a deliberate change, not drift.

## 6. Reversibility and smallest safe prototype

The entry-point form is reversible (it is a build+unit change, no persistent
state). Smallest safe prototype after approval: a disposable oneshot unit on the
x86 dev article that renders config and exits `0`, with restart behavior left
unset pending `TBR-HA-01`.

## 7. Implementation acceptance criteria

The remaining change is `pyproject.toml`, the bounded module entry point, a
native oneshot with restart behavior omitted, image install wiring, and evidence
under `docs/evidence/findings/GAP-09D/`. Acceptance: the unit installs on the dev
image and reaches its declared state without prejudging
`TBR-HA-01`/`TBR-LINUX-01`.

## 8. Sources reviewed

`mule/__init__.py`, `mule/loops.py`, `pyproject.toml`,
`os/config/systemd-units.template`; `FML-ADR-051`, `FML-ADR-040`, `FML-ADR-029`;
`docs/decision-index.md` (`TBR-HA-01`, `TBR-LINUX-01` OPEN); REMEDIATION Phase 3,
line 648.

## 9. Owner disposition

`APPROVED` -- Program Owner approval recorded 2026-09-25. `FML-ADR-083` selects
the entry-point, installation/versioning model and unit shape. GAP-09D remains
open until the image-installed oneshot is exercised and closure evidence lands.
