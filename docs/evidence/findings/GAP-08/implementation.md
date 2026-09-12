# GAP-08 implementation record

**Finding:** GAP-08, eliminate documentation decision drift (P1).
**Evidence tier:** SIMULATED (documentation).

## Contradiction inventory (before editing)

Worked from the authoritative drift inventory in `CODEBASE-REPORT-2026-09-08.md`
§ 8, against the machine-readable state (trade frontmatter, findings register,
catalog.yml). Current-state contradictions found and corrected:

1. `docs/trades/README.md` status tables marked TBR-TAK-01, TBR-NET-01,
   TBR-NET-02, TBR-NET-03 as `OPEN` while their records are `CLOSED`; the
   no-hardware-work prose framed three closed trades as available work.
2. `ROADMAP.md` said TBR-TAK-01 "is open".
3. `README.md`: "Sixteen trades are open. Every one of them is unowned"
   (actual: 17 open, 1 unowned); "Nothing has been tested" (now tier-aware:
   nothing HARDWARE-VERIFIED); two hardcoded trade counts.
4. `docs/README.md` hardcoded "16 open trades".
5. `services/catalog/README.md` said "Empty. No service has been approved";
   `services/gateways/README.md` and `services/quadlets/README.md` echoed
   "no service selected"; all now reflect the catalogued OTS/Martin (FML-ADR-078).
6. `pyproject.toml` "no Python package"; `test/README.md` "no application code
   has been written" -- both contradicted by `mule/`.
7. Owner drift: closed trades TBR-TAK-01/TBR-NET-01 showed `TBD-SRR` in prose or
   the register table while frontmatter names the owner; a closed trade cannot
   carry `TBD-SRR`.
8. `os/ansible/inventory/example.yml` said TBR-NET-01 is open (closed, FML-ADR-063).

Counts that would rot were replaced with a pointer to generated `STATUS.md`
rather than a new hardcoded number.

## Closure is gated (not yet CLOSED)

Independent reviewer sampling found the remaining references to these closed
trades live in three categories that are **not** unambiguous synchronization,
so per the GAP-08 user gate they are presented rather than edited unilaterally:

- **An architecture statement:** `FML-ADR-060` is `CONDITIONAL` "while TBR-NET-01
  remains open". TBR-NET-01 has closed; whether that resolves the ADR's condition
  is an architecture decision for the Program Owner.
- **Trade-record reasoning:** the closed `TBR-NET-03` body reasons about
  TBR-NET-01 being open at decision time.
- **Historical evidence:** dated `docs/evidence/TBR-NET-03/` artifacts recorded
  what was true when written.

GAP-08 therefore stays IMPLEMENTED: current-state drift is corrected and the
trade-state category is machine-enforced, but "zero known contradictions" closure
waits on the owner's call on FML-ADR-060 and on a policy for historical prose.

## Corrections

- `docs/trades/README.md`: the four stale status cells set to `CLOSED`; the
  no-hardware section rewritten to state those three are closed (with their
  controlling ADRs) and TBR-ID-01 is the one that remains open.
- `services/catalog/README.md`: describes the two catalogued services as a
  contract, deployment gated on their trades.
- `README.md`: no longer hardcodes a trade count; points at the generated
  `STATUS.md` for the current number.

## New enforcement (so this category cannot silently return)

- `tools/validate-trade-states.py`: every trade-status cell in
  `docs/trades/README.md` must match the trade record's frontmatter `status`;
  wired into `validate-docs.sh` (check 24). The trade records are authoritative.

## Failing-first demonstration

`validate-docs catches the trades page stating a closed trade as open` (bats)
flips a CLOSED cell back to `OPEN` in a sandbox and asserts the check fires
naming the trade. Observed firing directly before the fixes as well.

## Reproduce

`bash tools/validate-docs.sh`; `bats test/unit`. All generated docs reproduce
without diff (`gen-*.sh --check`). SIMULATED.
