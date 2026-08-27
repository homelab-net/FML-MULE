# United States, 902-928 MHz

**Status: seeded, `UNVERIFIED`, every value `TBD`.**

This profile exists because the United States 902-928 MHz allocation is the
region the program's first hardware is being sourced for. It is **not** the
reference region and **not** a default.

SAD section 8.1 confirms what makes this region's profile load-bearing:
**HaLow and LoRa may share the 902-928 MHz US band** and must be treated as
colocated potentially interfering systems. The prototype BOM sources both a
US915 HaLow module and a US915 LoRa module, so the two occupy the same band in
the same enclosure by construction. The program does not treat any region
as canonical; doing so is how other regions become second-class and then
unmaintained.

Nothing in this directory has been verified. No channel plan has been selected,
no module has been qualified, and no measurement has been taken. Every
parameter in `profile.yml` reads `TBD`, and that is an accurate statement of
the program's knowledge rather than an unfinished chore.

## Regulator and framework

**Regulator:** Federal Communications Commission (FCC).

Sub-GHz short-range operation in this band is addressed in 47 CFR Part 15, with
the Part 15.247 and 15.249 provisions commonly cited for this class of device.
Amateur service rules are in 47 CFR Part 97; Part 97.113 addresses prohibited
transmissions, including messages encoded to obscure meaning.

Those citations are orientation. **They have not been read against this
program's specific configuration**, and the applicable subsections, power
limits, and hopping or digital-modulation requirements are `TBD`. A contributor
who reads the rules against a candidate module and records what applies would
be doing genuinely useful work.

## What is unknown, and what will decide it

| Unknown | Trade |
| --- | --- |
| Channel plan within the band | `TBR-RF-02` |
| Coexistence with the LoRa plane in the same band | `TBR-RF-02` |
| The **stated LoRa availability or duty-cycle figure** to hold while HaLow reacquires | `TBR-RF-02` |
| Permitted and qualified radio modules | `TBR-HW-01` |
| Antenna and gain, and the integration conditions of the approval | `TBR-HW-01` |
| Conventional Wi-Fi channel selection for mesh and access point | `TBR-RF-01`, `TBR-RF-03` |
| Radiofrequency exposure evaluation for the assembled device | `TBR-HW-01` |

## Amateur radio

Amateur integration is **disabled by default**, here as everywhere.

The specific conflict for this region is worth stating plainly: encrypted
traffic, and more broadly any transmission whose purpose is to obscure meaning,
is not permitted on amateur allocations in the United States. A builder cannot
enable amateur-band operation and confidential mission traffic simultaneously
and remain lawful. The design consequence of that conflict is `TBD`; see
`THREAT_MODEL.md` and `REGULATORY.md`.

## What this profile does not do

It does not make a device compliant, and it does not authorise operation on any
frequency. Compliance of the assembled device is the builder's responsibility,
including module approval, antenna and gain, integration conditions and
labelling. See `REGULATORY.md`.

## The coexistence priority

CONOPS section 36 fixes the operational priority for this band:

> When IP connectivity is lost, preservation of the degraded LoRa communications
> path takes priority over aggressive HaLow reacquisition behavior that would
> materially impair LoRa reception.

CONOPS section 36 further requires System Architecture to **state a LoRa
availability or duty-cycle figure** to be maintained while HaLow reacquisition
is active, so the coexistence design has a verifiable target. That figure does
not exist yet; producing it is `TBR-RF-02`.

`FML-ADR-027` adds that coexistence is controlled through **documented supported
host and radio interfaces**, and that the architecture shall not assume
`openmanetd` provides deterministic scan or transmit-suppression primitives.

## Contributing to this profile

The most useful contributions, in order:

1. Read the applicable Part 15 subsections against a specific candidate module
   and record which apply, with citations. Archive the rule text under
   `docs/evidence/`.
2. Record module approval identifiers, antennas and gains for candidate
   hardware, feeding `TBR-HW-01`.
3. Take the coexistence measurements `TBR-RF-02` asks for, in an assembled
   enclosure rather than on a bench.

The first of these needs no hardware.
