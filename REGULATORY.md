# Regulatory considerations

This document is written for builders. It is not legal advice, and nobody
associated with this program is acting as your counsel or as your regulator.
Radio regulation is national, it changes, and the authoritative source is
always your own administration's current rules. If this document and your
national rules disagree, your national rules are correct and this document is
wrong.

Read this before you buy hardware, not after.

## The band this program targets is region-specific

The Wi-Fi HaLow (IEEE 802.11ah) hardware referenced in this repository operates
in **902-928 MHz**. That allocation exists in the United States and in a number
of other administrations. It does **not** exist for this purpose in the
European Union or the United Kingdom, which use **863-868 MHz** for the
equivalent short-range-device role, with different channel widths, different
power limits, and in many sub-bands a **duty-cycle constraint** that has no
analogue in the 902-928 MHz rules.

A design that assumes 902-928 MHz is unusable by a large share of potential
contributors, and building one anyway is a decision to exclude them. For that
reason:

- Region is an **input to configuration generation**, not a constant. See
  `regions/README.md`.
- `regions/us-915/` is seeded because it is the region the first hardware is
  being sourced for. It is not the reference region, and it is not the default
  in any sense other than being first.
- A contributor adding a region copies `regions/_template/`.
- No configuration file in `os/config/` hardcodes a frequency, a channel, a
  bandwidth, or a transmit power. Those come from the region profile.

The 863-868 MHz profile is `TBD` and requires a contributor who can source and
test compliant hardware. See `regions/README.md`.

## Modular certification and the assembled device

Most radio modules that a builder can buy carry a **modular approval**. That
approval is granted against a specific test configuration, and it typically
includes the antenna, or a defined class of antenna, and a maximum gain.

Three consequences follow, and all three are commonly got wrong:

1. **Substituting an antenna can void the modular approval.** A higher-gain
   antenna raises radiated power. An antenna of a different type may fall
   outside the approval's permitted class. "It has the same connector" is not
   a compliance argument.
2. **Integration conditions are part of the approval.** These may cover
   shielding, ground plane, separation distance from a user, and labelling.
   Ignoring them removes the basis on which the module was approved.
3. **Compliance of the assembled device is the builder's responsibility.**
   Combining several individually approved modules in one enclosure does not
   automatically produce a compliant device, particularly where emitters
   interact or where the assembly must be labelled as a whole.

This program targets a design where each qualified hardware block records its
antenna, gain, and integration conditions in `hardware/blocks/<block-id>/rf/`.
Those records are currently `TBD` because no block has been selected. See
`TBR-HW-01` and `TBR-RF-01`.

## Radiofrequency exposure

A multi-emitter device carried or operated near people raises RF exposure
questions that a single-radio device may not. Simultaneous transmission from
several bearers is the normal operating mode for MULE, not an edge case.
Exposure evaluation for the assembled device is `TBD` and is an input to
`TBR-HW-01`. No exposure claim of any kind is made in this repository.

## Amateur radio integration

Amateur-radio integration is **disabled by default** in every configuration
this program ships. Where a builder enables it, in a jurisdiction that permits
it:

- Operation requires an appropriately licensed **control operator** who is
  responsible for the station.
- **Station identification** obligations apply, at the interval and in the form
  the licence requires. Automated systems do not exempt an operator from this.
- **Content is restricted.** Amateur allocations are not general-purpose
  carriage. Business communications are prohibited in many jurisdictions.
- **Encryption, or any transmission whose purpose is to obscure meaning, is not
  permitted on amateur allocations in many jurisdictions**, including the
  United States. This directly conflicts with the confidentiality properties of
  the mission-services plane. A builder cannot enable amateur-band operation
  and confidential mission traffic simultaneously and remain lawful in those
  jurisdictions. The design consequence of that conflict is `TBD`; see
  `THREAT_MODEL.md` and `TBR-RF-02`.
- Third-party traffic rules may restrict who may pass messages through the
  station and to which countries.

Nothing in this repository should be read as asserting that any amateur
allocation is available for the traffic MULE carries.

## Public-safety and interoperability frequencies

**No public-safety, emergency-services, or interoperability frequency is
authorised merely because it appears in a reference document.** Appearance in a
national interoperability channel plan is a description of an allocation, not a
grant of permission to transmit on it. Use of those channels requires
authorisation from the licensee or the responsible agency, and in most cases
type-accepted equipment that this program does not produce.

Volunteer organisations frequently misunderstand this. If your group intends to
operate on a public-safety allocation, that is a written arrangement with the
agency holding the licence, negotiated before the exercise, not a configuration
setting.

## Licence-free and unlicensed operation is not unregulated operation

Operating under an unlicensed allocation still imposes obligations: power
limits, bandwidth limits, duty-cycle limits where applicable, an obligation to
accept interference, and an obligation not to cause harmful interference to
licensed services. A device that meets its limits can still be required to stop
transmitting.

## Builder responsibilities

You are responsible for:

- Determining which rules apply where you operate.
- Verifying that each module you fit is approved for use in your region.
- Verifying that your antenna and integration keep that approval valid.
- Labelling, where your rules require it.
- Ceasing operation if you are told your device causes harmful interference.
- Any exercise or deployment authorisation your operating context requires.

## Country notes

This section is deliberately short and is expected to be extended by
contributors who actually operate in the region concerned. Add a subsection
only for a region you can speak to, cite the rule you are describing, and do
not summarise a rule you have not read.

Every entry here is `UNVERIFIED` by this program. These are orientation notes
pointing you at the right regulator, not a compliance determination.

### United States

Sub-GHz short-range operation is addressed in 47 CFR Part 15, with 902-928 MHz
Part 15.247 and 15.249 provisions commonly cited for this class of device.
Amateur service rules are in 47 CFR Part 97; Part 97.113 addresses prohibited
transmissions, including messages encoded to obscure meaning. Regulator: FCC.
Detail is `TBD`; see `regions/us-915/`.

### European Union

The equivalent short-range-device allocation is 863-868 MHz, governed by the
Radio Equipment Directive and by harmonised standards under EN 300 220, with
duty-cycle limits that vary by sub-band. 902-928 MHz is not available for this
purpose. Regulator: national administration, within the EU framework. No region
profile exists yet; see `regions/README.md`.

### United Kingdom

The relevant allocation is 863-868 MHz under the Ofcom licence-exempt
framework, following the EU sub-band structure closely but not identically.
902-928 MHz is not available for this purpose. Regulator: Ofcom. No region
profile exists yet.

### Add your region

Copy `regions/_template/`, fill in what you can verify, mark the rest `TBD`,
and open a pull request. A partial region profile with honest gaps is more
useful than none.
