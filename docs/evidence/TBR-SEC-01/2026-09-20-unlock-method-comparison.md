# Protected-storage unlock: does it force a hardware root of trust?

**Tier:** analysis of the repository and the trade's own option set as they stand.
No measurement, and **nothing here selects a mechanism or closes the trade**. It
banks the hardware-free ("larger") half of `TBR-SEC-01`, the way
`docs/evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md`
banked the size half of `TBR-COMP-01`.

**Date:** 2026-09-20. **Trade:** `TBR-SEC-01`. **Taken by:** Cameron Zobrist.
**Source:** SAD v0.31 section 27.5.2 (the fixed option set and the closure
criteria); `FML-ADR-043`, `FML-ADR-044`, `FML-ADR-041`, `FML-ADR-042`;
`THREAT_MODEL.md` (physical capture); and the prior trade evidence
`2026-08-31-two-credentials-have-no-origin.md`.

## The one question this answers

`FML-ADR-043` requires LUKS2-class data-at-rest and rejects an unattended key
stored plainly on the same media. That leaves the unlock method open, and
`TBR-SEC-01` must be settled **before the hardware block is locked** because it
`feeds: [TBR-HW-01, TBR-CARRIER-01]` and may add a hardware root of trust to the
carrier. So the procurement-gating question, ahead of any on-hardware demo, is:

> **Does the unlock method force a hardware root of trust (TPM 2.0 / secure
> element) onto the carrier, and by when must that be decided?**

## The four options, only as far as they bear on that question

SAD section 27.5.2 fixes the option set. What matters for the carrier is whether
an option can satisfy **unattended field restart** (a headless node reboots after
a brownout or battery change with no operator, no network) without keeping the key
on the device -- because that is the requirement that separates the options.

| Option | Hardware root of trust on carrier? | Unattended restart? | Captured **running** node | Pulled media |
| --- | --- | --- | --- | --- |
| 1. Operator passphrase | **No** | **No** -- needs a human at each boot | protected only if locked | protected |
| 2. TPM 2.0 sealed key | **Yes** (TPM 2.0) | Yes (seal to boot state) | **not** protected (unlocked) | protected |
| 3. Secure-element-assisted | **Yes** (secure element) | Yes | **not** protected (unlocked) | protected |
| 4. Combination (seal + operator auth) | **Yes** | Partial (some ops need operator) | best of the set, still not full | protected |

The pattern is decisive: **every option that meets unattended restart requires a
hardware root of trust.** The only option with no carrier impact -- the operator
passphrase -- is, in the trade's own words, "incompatible with unattended
operation." A headless captured-risk node that must come back after a brownout is
exactly the case SAD 27.5.2 puts first.

`THREAT_MODEL.md` (physical capture) bounds what even the hardware options buy: a
node captured while **running** is captured **unlocked**, and the program assumes
a captured node yields its keys. So a hardware root of trust protects pulled media
and enables unattended boot; it does **not** by itself defeat capture-while-running.
That is a decided limitation, not a finding of this artifact.

## The interactions the trade must carry (and the carrier must not break)

- **Rollback (`FML-ADR-041`).** Whatever unlocks the active root must also unlock
  the known-good path, or rollback becomes a way to boot without protections. A
  seal-to-boot-state scheme (option 2/3) has to seal to **both** roots, or an
  update that changes the measured boot state locks the node out of its own
  fallback. This is a real constraint on a TPM/secure-element measured-boot design.
- **Time (`FML-ADR-042`).** If unlock depends on trust validation, a dead clock
  battery becomes a node that will not unlock. Any hardware-sealed scheme that also
  gates on validity inherits this; the carrier RTC/battery choice (`TBR-HW-01`)
  interacts here.
- **Zeroize (`FML-ADR-044`).** Cryptographic erase only works if destroying the
  key material actually denies the data -- which is exactly why option 1's
  key-beside-data arrangement is rejected and why the hardware options must expose
  a key path that zeroize can invalidate without WAN.

## The answer, for `TBR-HW-01` / `TBR-CARRIER-01`

**If unattended field restart is a hard requirement -- which the CONOPS headless,
no-reachback posture implies -- then a hardware root of trust (TPM 2.0 or a secure
element) becomes a carrier requirement, and `TBR-CARRIER-01` must reserve that
provision before the board is locked.** The alternative the owner may instead
accept is passphrase-only unlock with **no** unattended operation, a usability
cost `FML-ADR-043`'s fallback already names. There is no middle option that is
both unattended and free of a hardware root of trust.

**Decision timing:** this must be resolved **before `TBR-CARRIER-01` locks the
carrier** (a TPM header / secure-element footprint cannot be added after the board
is chosen). `TBR-SEC-01`'s target date is 2026-09-30; the carrier-provision call
is the part that cannot slip past board selection.

## What this does not do

- **Does not close `TBR-SEC-01`.** Closure requires the on-hardware evidence SAD
  27.5.2 lists: demonstrated unlock and boot on candidate hardware, the rollback
  path under the same scheme, behaviour on a non-credible clock, and the zeroize
  test. Those are hardware-gated and remain open. The trade stays `OPEN`.
- **Does not select a mechanism.** It compares the trade's own options and hands
  the root-of-trust question to the owner and `TBR-HW-01`/`TBR-CARRIER-01`.
- **Does not resolve fleet rekey or credential issuance.** SAD 27.5.2 lists fleet
  rekey in scope, but `2026-08-31-two-credentials-have-no-origin.md` already
  records that whether this trade **absorbs credential issuance/rotation** is an
  owner register decision that belongs to the identity plane, not the unlock trade.
  This artifact surfaces that line and stops at it.

## What this unblocks

The carrier-provision input to `TBR-HW-01` / `TBR-CARRIER-01`: the program can
decide, now and on paper, whether the prototype carrier must carry a TPM 2.0 or
secure-element provision, rather than discovering it after board selection. It is
an owner decision informed by this comparison, not a closure of the trade.
