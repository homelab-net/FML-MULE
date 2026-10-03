# Evidence

Trades and remediation findings close on evidence, and evidence lives here.
Trade directories are named exactly for the trade ID. Finding packets live
under `findings/<ID>/` so they cannot be mistaken for trade evidence.

A closure that cites no path under `docs/evidence/` is not a closure. That rule
is in `CONTRIBUTING.md`, in `docs/trades/README.md`, and in `AGENTS.md`, because
it is the rule most likely to be quietly skipped by someone who is confident
and in a hurry.

## Why the evidence is copied in rather than linked

**Vendors delete PDFs and discontinue parts.** This program has already had a
key module reach end of life before it could be purchased. A closure claim whose
supporting datasheet has since 404'd is not verifiable, and a reader two years
from now cannot tell whether the claim was ever sound.

So: archive the document into the repository at the moment you cite it, not
when you next need it. Record the URL and the retrieval date alongside, so the
provenance survives even though the link will not.

Third-party documents keep their original licence. See `LICENSE-DOCS`.

Records written before the software-composition rename use "flat-sat",
`test/flatsat/`, and `FlatSatNode` for what is now the software digital twin.
Those words, paths, and commands are left as they were when the record was
written. See `docs/glossary.md`.

## Directory layout

```text
docs/evidence/
  README.md
  TBR-LINUX-01/
    README.md            what this trade's evidence set contains
    2026-01-15-build-log-kernel-6.x.txt
    2026-01-15-dmesg-node-01.txt
    datasheets/
      vendor-part-rev-b.pdf
      vendor-part-rev-b.SOURCE.md
  TBR-PWR-01/
    ...
  findings/
    README.md
    BASE-01/
      closure.md
      2026-09-09-verification.json
```

Every trade directory exists from the start, with a `README.md` stating what
that trade's closure gate demands. They are not empty placeholders waiting to
be created; the gate is written down before the work, so the answer cannot be
graded against a standard invented after seeing it.

Finding directories are created when they first hold evidence. Their
`closure.md` frontmatter is validated against
`docs/findings/closure-packet.schema.json`; raw artifacts named by the packet
are hash-checked. See `docs/findings/README.md`.

## Naming

`YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`

Dates first so a directory listing sorts chronologically. No spaces. Lower
case. Where a file relates to a specific node, name it.

## What a measurement record must contain

An unlabelled number in a text file is not evidence. Every measurement records:

- **What was measured**, in terms someone else could repeat.
- **Instrument**, including model and, where it matters, calibration date.
- **Date and time.**
- **Node identifier** and **image build identifier**.
- **Configuration**: region profile, channel, transmit power, antenna,
  separation, orientation.
- **Ambient conditions** where they could plausibly matter, which for this
  program is most of the time.
- **Who took it.**

Raw output is preferred over a summary. Commit the log; write the summary in
the trade file.

**One half of this is now machine-checked.** It was a `[review]` rule and it was
broken on 2026-10-02: `TBR-NET-02/2026-10-02-three-node-lab-observations.json`
published RSSI and SNR figures while the same file recorded the antenna,
orientation and separation as "Not recorded" and the ambient conditions and EIRP
as "Not measured". A reviewer caught it; nothing here could.
`tools/validate-docs.sh` check 25 now fails any artifact that **both** publishes
a received-signal figure **and** disclaims the configuration that figure has to
be read against.

It checks the shape of that failure, not the whole contract. Either half alone
still passes, and should: `TBR-NET-02/2026-09-27-one-lora-hop-to-a-partner-node.md`
names its antenna, separation, orientation and ambient conditions and publishes
its figures on that basis, and a record that lacks the geometry may say so as
long as it withholds the figures. Everything else in the list above —
instrument, date, node, who took it — is still on whoever reads the diff.

## What else belongs here

- **Logs.** `dmesg`, `journalctl`, `batctl`, `iw`, build output. Scrub before
  committing; see below.
- **Photographs.** Antenna placement, thermal setup, an assembly step that a
  written instruction cannot convey, damage. Tracked by Git LFS per
  `.gitattributes`.
- **Archived vendor datasheets**, in a `datasheets/` subdirectory, each with a
  `.SOURCE.md` recording the URL, the retrieval date, the document revision,
  and who retrieved it.
- **Written analysis**, for trades that close on reasoning rather than
  measurement. `TBR-TAK-01` and `TBR-NET-01` are both of this kind, and their
  evidence is a document, not a number.

## What does not belong here

The publication rule in `SECURITY.md` applies without exception:

- No real deployment location. A photograph with a recognisable landmark, or
  with GPS metadata intact, discloses one. Strip metadata before committing.
- No real member identity or callsign. Redact from logs and from photographs.
- No credential, key, or certificate. A `journalctl` excerpt can contain one.
- No captured operational traffic from a real deployment.

Record what you scrubbed. A log with an obvious redaction is honest; a log
silently trimmed is not reviewable.

**Two tools now stand behind that rule, because it had nothing behind it.**
`tools/scrub-telemetry.py` redacts the identifiers from a
`test/bench/capture-telemetry.py` document, replacing each with a visible token
and attaching a `scrub_manifest` recording what went and what deliberately
stayed. `tools/validate-identifiers.py` runs in `tools/lint.sh` and **fails the
build** when something under `docs/evidence/`, `test/fixtures/` or
`test/results/` still carries one, because the secret scanner does not look for
MAC addresses.

It refuses an equipment identifier, not every address-shaped string. A
universally administered MAC names a real part; the locally administered ones
that `mac80211_hwsim` and `veth` invent name nothing, and 45 of them are already
committed here. Failing on those would mean scrubbing meaningless values across
most of this directory, which is how a check gets ignored.

The case worth knowing about: **an IPv6 link-local address defeats a MAC
pattern.** An `fe80::` address in EUI-64 form contains no MAC-shaped text and
reconstructs the hardware address exactly -- one beginning `fe80::dea6:32ff:fe…`
decodes to a MAC beginning `dc:a6:32:…`, the Raspberry Pi OUI. That is the leak
a capture from an arm64 article actually produces, so both tools decode rather
than matching on shape.

The addresses above are deliberately truncated, and finding out why is the
shortest demonstration that the check works: written in full, they tripped it in
this very file the first time it ran. Documentation that lives under a scanned
directory has to illustrate the shape without carrying a whole identifier.

## Evidence for a trade that closes against a fake

Some evidence is legitimately produced against fakes and fixtures rather than
hardware, per the hardware abstraction rule in `AGENTS.md`. That is acceptable
where the trade's closure gate says so, and it must be stated plainly in the
evidence README: what was fake, what was real, and what that leaves unverified.

Evidence produced against a fake never supports a claim about physical
behaviour.
