# Evidence

Trades close on evidence, and evidence lives here. One directory per trade,
named exactly for the trade ID.

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
```

Every trade directory exists from the start, with a `README.md` stating what
that trade's closure gate demands. They are not empty placeholders waiting to
be created; the gate is written down before the work, so the answer cannot be
graded against a standard invented after seeing it.

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

## Evidence for a trade that closes against a fake

Some evidence is legitimately produced against fakes and fixtures rather than
hardware, per the hardware abstraction rule in `AGENTS.md`. That is acceptable
where the trade's closure gate says so, and it must be stated plainly in the
evidence README: what was fake, what was real, and what that leaves unverified.

Evidence produced against a fake never supports a claim about physical
behaviour.
