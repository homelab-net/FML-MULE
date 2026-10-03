# Bench AP band coexistence, and what the AP radio actually advertises

**Tier:** `UNVERIFIED` for any throughput claim; the configuration readings
below are direct device and regulatory-domain queries on real hardware.
**Status:** observation record. Nothing here closes `TBR-RF-03`.
**Date:** 2026-10-03. **Node:** the x86 bench article. **Trade:** `TBR-RF-03`.

**Why this exists.** The Program Owner reported that reaching the WAN through
the bench access point is very slow. The cause is a band-coexistence condition
on the bench, and diagnosing it produced three readings about the AP radio that
`TBR-RF-03`'s open hardware half needs. `AGENTS.md` names the Linux/radio
boundary and RF coexistence as the program's dominant uncertainty; this is an
observation at that boundary, taken from a report rather than designed.

## 1. What was found

Both radios on the bench were operating in the 2.4 GHz band at the same time:

| Role | Band and channel | Width |
| --- | --- | --- |
| EUD access point | 2.4 GHz channel 11 (2462 MHz) | 20 MHz |
| WAN uplink (station) | 2.4 GHz channel 4 (2427 MHz) | 20 MHz |

Every EUD byte is therefore received on 2.4 GHz and retransmitted on 2.4 GHz by
a second radio in the same chassis. The two 20 MHz channels do not overlap in
spectrum -- channel 4 spans 2417-2437 MHz and channel 11 spans 2452-2472 MHz --
so this is **not** a co-channel interference claim. It is adjacent-band
operation between co-located transmitters, plus a relay whose two legs share one
band, and the AP leg is additionally held at 20 MHz.

**The access point was running a configuration the program has already decided
against.** `docs/evidence/TBR-RF-03/2026-09-21-ap-channel-and-eirp-decision-packet.md`
is `DECIDED` and sets the AP to channel 149; `regions/us-915/profile.yml`
carries it, and `nodes/pi-mule-1/node.yml` carries `ap_channel: 149`. The live
bench AP was on channel 11. This is the deviation class recorded in
`docs/dev-machine.md`: a bench left at a default is not neutral, it is
exercising the option the program rejected.

## 2. The AP radio advertises the decided channel, and 80 MHz

Queried from the driver's own capability advertisement rather than a product
page. The adapter presents as `rtl8812au`, an out-of-tree driver.

- Two bands present. The 5 GHz band lists **5745 MHz (channel 149)** with
  neither a DFS `radar detection` flag nor a `no IR` flag. The channels above
  165 do carry `no IR`, and 5260-5720 MHz all carry `radar detection`, so 149 is
  usable for a beaconing AP without DFS obligations.
- VHT is advertised, including short guard interval at 80 MHz, and the radio
  reports a highest supported VHT receive rate of 867 Mbps.
- The regulatory domain is `country US: DFS-FCC`, whose `5730 - 5850` entry
  permits 80 MHz. Channel 149 is the lowest member of the 149/153/157/161 block,
  whose 80 MHz centre is channel 155.

So the decided channel is reachable on this adapter at 80 MHz. This is a
statement about what the radio and the regulatory domain allow, not a
measurement of a link.

## 3. The per-channel power ceiling is lower at 149 than at the 2.4 GHz channel

The adapter advertised a 20.00 dBm transmit power while on channel 11, and the
5 GHz entries each carry a 15.0 dBm per-channel figure. These are the driver's
configured and advertised ceilings read back from the device, not radiated
measurements, and nothing on this bench can measure EIRP. The decision packet
is explicit that antenna gain raises radiated power and that the profile's
`ap_max_eirp_dbm` is a planning value; this record does not revise it.

The trade-off is therefore real and should be recorded before anyone treats the
band move as free: moving the AP to 149 buys band separation from the uplink and
80 MHz of width, and costs 5 dB of advertised transmit ceiling.

## 4. A reading this platform cannot provide

`iw station dump` against the AP interface returns a received-signal figure for
an associated station and **no `tx bitrate` or `rx bitrate` line at all**. The
out-of-tree `rtl8812au` driver does not report per-station rate information
through nl80211.

The consequence is a limit on evidence, not a defect to work around: the
negotiated rate on the EUD leg cannot be read from the AP on this adapter, so a
before-and-after rate comparison across the band move is not available from the
driver. Any throughput claim for this leg has to come from an endpoint
measurement instead. This belongs in `docs/readings.md` as a reading whose
platform answer is absent, and it is the `T | None` case that
`AGENTS.md` characteristic failure 5 is about: the honest return is "cannot
tell", not a zero.

## 5. What is withheld, and why

Received-signal figures were observed for the uplink station and for a phone
associated to the AP, and negotiated bitrates were observed for the uplink. They
are **withheld**.

`docs/evidence/README.md` requires a measurement record to carry the antenna
model, separation, orientation, transmit power and ambient conditions the figure
must be read against. The antenna model, separation and orientation of the
phone, of the bench, and of the home access point were not recorded before the
observation, and `AGENTS.md` is explicit that afterwards the geometry is gone
and the number is unpublishable. Publishing them would also make this artifact
fail check 25, correctly.

What this costs: the claim "the uplink is not the bottleneck" is **supported but
not published** here. It rests on withheld figures. A repeat with geometry
recorded first would publish them.

## 6. What this does and does not establish

Established, on real hardware:

- Both bench radios were in the 2.4 GHz band simultaneously, with the AP on a
  channel the program had already decided against.
- The AP adapter advertises channel 149 without DFS or no-IR restriction, and
  advertises VHT with 80 MHz support in a regulatory domain that permits it.
- The adapter advertises a lower per-channel transmit ceiling at 5 GHz than the
  figure it reported on 2.4 GHz.
- The `rtl8812au` driver reports no per-station bitrate through nl80211.

Not established, and not claimed:

- **No throughput figure, before or after.** None was measured; the EUD-leg rate
  cannot be read from this driver, and no endpoint measurement was taken.
- **That the band move fixes the reported slowness.** The coexistence condition
  is documented and the mechanism is sound, but the remedy is untested here. The
  Owner's report is a report, not a measurement.
- **Nothing about radiated power.** No EIRP was measured and none can be on this
  bench.
- **Nothing about the mesh half of `TBR-RF-03`.** Whether AP and mesh share one
  radio is untouched by this record. No radio in the lab supports
  `mesh point`.
- **Nothing about the Raspberry Pi article.** This is one out-of-tree driver on
  x86. `brcmfmac` on the Pi is a different radio with a different capability set,
  and is already recorded as single-channel.

## 7. Consequences worth acting on

1. The bench AP should run the decided channel 149, so that bench results
   describe the configuration the program chose.
2. `test/bench/mule-ap-up.sh` emits `ieee80211n=1` and no VHT directives, so it
   would bring an AP up at 20 MHz even on channel 149. Making it emit VHT cannot
   be unconditional: `hostapd` refuses to start when `ieee80211ac=1` is set on a
   radio that does not advertise VHT, and the Pi's radio is not this one. That is
   a change needing its own evidence, not a quiet edit.
3. The divergence between the running bench AP and the repository is another
   instance of the reconciliation item: the live `hostapd` was started from a
   predictable `/tmp` path by an older copy of the bring-up script, and the live
   `dnsmasq` carries options the repository's script does not generate.
