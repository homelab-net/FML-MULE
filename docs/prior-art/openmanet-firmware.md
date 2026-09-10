# OpenMANET firmware

**Evaluated:** 2026-09-10 at release `1.8.0`, commit
`365b27618459e50f3b56f71effd124f6cb3b86f4`. **Verdict:** retain as the
reference configuration and comparative prototype selected by `FML-ADR-023`;
do not adopt it as the production image.

## Fit

OpenMANET firmware is an OpenWrt 24.10-derived whole-system image for supported
single-board computers and HaLow radios. Its common build configuration selects
the OpenMANET Morse stack, `openmanetd`, `gpsd`, Alfred, `batctl`, Tailscale and
mesh-capable WPA tooling. Its feed file pins the OpenMANET, Morse Micro,
OpenWrt, LuCI, routing and telephony sources to exact commits.

This is directly relevant configuration knowledge for `FML-REQ-001`,
`FML-REQ-011`, `FML-REQ-012` and `FML-REQ-032`. It is not the selected MULE
host: `FML-ADR-022` selects Debian stable, and `FML-ADR-023` expressly makes
OpenMANET a reference and prototype rather than a mandatory production image.
`FML-ADR-040` also requires the field kernel, radio driver, radio firmware and
userspace tooling to pass the MULE compatibility-set promotion gate together.

## Reusable work

Reuse is limited to configuration knowledge and comparative evidence:

- board and HaLow driver configuration;
- package selection and exact upstream feed pins;
- mesh, multicast and ATAK-oriented defaults; and
- a reference image against which native Debian behavior can be compared.

Porting the OpenWrt/UCI image or maintaining a private fork would contradict
`FML-ADR-023`. Any source-level fix that must be carried instead of expressed
as configuration enters the fork register with an owner.

## Intake result

- License: GPL-3.0 for this repository; the image is an aggregate of separately
  licensed packages, so the bundled license review remains pending.
- Maintenance: five releases were published between 2026-03-14 and
  2026-08-16. The GitHub contributor summary is heavily concentrated in one
  maintainer account.
- Platform: the pinned README names Raspberry Pi, HaLowLink, Heltec and Gateworks
  targets; build configuration supplies the exact board profiles.
- Resources: not measured. Board storage values in build configuration and
  upstream qualitative hardware notes are not MULE resource measurements.
- Runtime and data: this is an operating-system image, not a contained service.
  exposed services, credentials, persistence and upgrade behavior depend on the
  selected board and package configuration and require image inspection.
- Security: no repository security advisory was published through GitHub's
  advisory endpoint on 2026-09-10. No independent audit or repository SBOM was
  identified in the pinned artifact.
- Prototype: not run in this intake. Comparative image bring-up belongs to the
  Stage 2 mesh-equivalence and compatibility-set gates.

## Exit strategy and questions

Keep the immutable source reference and reproduce accepted behavior through the
MULE Debian build. An upstream image may be retained on the bench only as a
comparison point. The unresolved questions are which configuration deltas
Debian needs and whether any delta requires a maintained patch rather than
ordinary configuration.

## Sources

- [Pinned README](https://github.com/OpenMANET/firmware/blob/365b27618459e50f3b56f71effd124f6cb3b86f4/README.md)
- [Pinned feed set](https://github.com/OpenMANET/firmware/blob/365b27618459e50f3b56f71effd124f6cb3b86f4/feeds.conf.default)
- [Pinned setup script](https://github.com/OpenMANET/firmware/blob/365b27618459e50f3b56f71effd124f6cb3b86f4/scripts/openmanet_setup.sh)
- [Pinned common package configuration](https://github.com/OpenMANET/firmware/blob/365b27618459e50f3b56f71effd124f6cb3b86f4/boards/common/openmanet_diffconfig)
- [Release history](https://github.com/OpenMANET/firmware/releases)
- [Contributor summary](https://api.github.com/repos/OpenMANET/firmware/contributors)
- [Repository security advisories](https://github.com/OpenMANET/firmware/security/advisories)
