# Regions

**Region is a parameter, not a constant.**

The sub-GHz band this program targets is region-specific. 902-928 MHz exists in
the United States and a number of other administrations. It does **not** exist
for this purpose in the European Union or the United Kingdom, which use
863-868 MHz with different channel widths, different power limits, and
duty-cycle constraints that have no analogue in the 902-928 MHz rules.

A repository hardcoded to one band is unusable by a large share of potential
contributors. Building one anyway is a decision to exclude them, and it is a
decision that becomes very expensive to reverse once configuration,
documentation and hardware selection have all assumed a single band.

So: a region profile is an **input to configuration generation**. No file in
`os/config/` contains a frequency, a channel, a bandwidth, or a transmit power.
Those values come from `regions/<region-id>/`.

Read `REGULATORY.md` before using anything in this directory. It is not legal
advice, and neither is this.

## What a region profile holds

| File | Contents |
| --- | --- |
| `README.md` | Regulatory context, the regulator, what is verified and what is not. |
| `profile.yml` | Machine-readable parameters consumed by configuration generation. |
| `channel-plan.md` | The channel plan, with the rule each entry derives from. |
| `modules.md` | Permitted radio modules, with approval identifiers and archived datasheets. |
| `constraints.md` | Duty cycle, power, antenna gain, and any other binding limit. |

## Regions present

| Region | Status | Notes |
| --- | --- | --- |
| `us-915` | Seeded, `TBD` throughout | 902-928 MHz. Seeded because it is the region the first hardware is being sourced for. |
| `_template` | Complete enough to copy | For a contributor adding a region. |

**`us-915` is not the reference region and is not a default.** It is first, and
that is all. The program does not treat any region as canonical, because doing
so is how the other regions become second-class and then unmaintained.

Every value in `us-915/` is currently `TBD`. No channel plan has been selected,
no module has been qualified, and no measurement has been taken. See
`TBR-RF-02` and `TBR-HW-01`.

## Regions wanted

**EU 863-868 MHz** and **UK 863-868 MHz** are the significant gaps. Both need a
contributor who can source and test compliant hardware in that region, because
neither can be written honestly by someone who cannot verify it. `REGULATORY.md`
records the orientation notes; a profile needs more than orientation.

The duty-cycle constraint in the European sub-bands is the part most likely to
have design consequences beyond configuration. A bearer that may transmit only
a small fraction of the time behaves differently enough that it may not support
the same operational concept. That question is not in any current trade, and it
should be; it is recorded here rather than being lost.

Other administrations that permit sub-GHz operation are equally welcome. A
partial profile with honest `TBD` entries is more useful than none.

## Adding a region

1. Copy `regions/_template/` to `regions/<region-id>/`. Use a short, stable
   identifier: the ISO country or economic area code, a hyphen, and the band's
   common name. For example `us-915`, `eu-868`, `au-915`.
2. Fill in what you can **verify against the rule itself**, not against a forum
   post or a vendor's marketing page. Cite the regulation, with its section.
3. Mark everything else `TBD`. Do not guess a power limit.
4. Archive any regulatory document you rely on into `docs/evidence/`, with its
   URL and retrieval date. Regulators reorganise their websites too.
5. Add a country note to `REGULATORY.md` pointing at the profile.
6. Open a pull request stating which region you can actually operate in. A
   profile written by someone who cannot test it should say so in its README.

## What a region profile does not do

A region profile does not make a device compliant. It records constraints so
that generated configuration respects them. Compliance of the assembled device
remains the builder's responsibility, including module approval, antenna and
gain, integration conditions and labelling. See `REGULATORY.md`.

Nor does a region profile authorise operation. A frequency appearing in a
channel plan is a description of an allocation, not permission to transmit on
it.
