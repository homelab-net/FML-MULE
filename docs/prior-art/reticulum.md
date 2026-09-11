# Reticulum

**Evaluated:** 2026-09-10 at release `1.5.2`, commit
`ea98db4f53dcf0defc0e71a16e60d28b1229c4e6`. **Verdict:** retain only as
architectural comparison material; do not use or incorporate the implementation.

## Fit

Reticulum is a user-space Python networking stack that supplies its own
cryptographic identity, addressing, routing and transport over heterogeneous
interfaces. IP can carry Reticulum, but Reticulum does not provide the IP bearer
that ATAK and the selected TAK service path require. Its RNode/LoRa path is also
separate from the upstream Meshtastic integration selected by `FML-ADR-026` and
`FML-ADR-070`.

That makes it useful comparison material for `TBR-ID-01` and `TBR-NET-04`, but
not a production component. Adding it would create a parallel client, identity
and routing ecosystem beside the standard ATAK/TAK, Meshtastic and IP paths,
contrary to `FML-ADR-048` and the upstream-first rule.

## License correction

The implementation is under the custom **Reticulum License**, not a public-domain
or OSI-approved license. The pinned license prohibits use in systems that include
the ability to purposefully harm human beings and prohibits direct or indirect
use in creating AI, machine-learning or language-model training datasets. Those
field-of-use restrictions make the implementation incompatible with unrestricted
FML reuse. The protocol was dedicated to the public domain, but upstream states
that the reference implementation is the authoritative specification; the
protocol dedication does not relicense the code.

The earlier note's description of the implementation as public-domain,
permissive and freely reusable was wrong and is superseded by this pinned-source
review. No implementation code or derivative is proposed.

## Intake result

- Maintenance: five releases were published between 2026-07-19 and 2026-08-29.
  The mirror's contributor summary is heavily concentrated in its maintainer.
- Platform: Python 3.7 or later, described as operating-system independent. The
  normal package depends on `cryptography` and `pyserial`; the separately named
  pure package omits declared dependencies.
- Runtime: local shared-instance and control endpoints default to TCP 37428 and
  37429; carrier interfaces add configuration-specific serial, TCP, UDP, KISS,
  RNode and other access. Interface authentication keys, network identity and
  the shared-instance RPC key are secrets.
- Data: configuration, identities, packet/resource caches and transport state
  live under the Reticulum configuration and storage tree. No operator backup
  or migration contract was identified in the pinned source.
- Resources: not measured for a MULE profile.
- Security: no repository advisory was published through GitHub's advisory
  endpoint on 2026-09-10. No independent audit or repository SBOM was identified.
- Prototype: not run. Running it would not change the license or architecture
  result.

## Exit strategy and questions

Retain links and conclusions only. Do not vendor, package or depend on the
implementation. If the program later adds a non-TAK operator messaging path,
that is a scope and architecture decision before any candidate evaluation. The
remaining comparison question is whether a public specification or independently
licensed implementation offers a useful identity or multi-bearer pattern without
importing this restricted implementation.

## Sources

- [Pinned README](https://github.com/markqvist/Reticulum/blob/ea98db4f53dcf0defc0e71a16e60d28b1229c4e6/README.md)
- [Pinned license](https://github.com/markqvist/Reticulum/blob/ea98db4f53dcf0defc0e71a16e60d28b1229c4e6/LICENSE)
- [Pinned package metadata](https://github.com/markqvist/Reticulum/blob/ea98db4f53dcf0defc0e71a16e60d28b1229c4e6/setup.py)
- [Pinned runtime configuration](https://github.com/markqvist/Reticulum/blob/ea98db4f53dcf0defc0e71a16e60d28b1229c4e6/RNS/Reticulum.py)
- [Release history](https://github.com/markqvist/Reticulum/releases)
- [Contributor summary](https://api.github.com/repos/markqvist/Reticulum/contributors)
- [Repository security advisories](https://github.com/markqvist/Reticulum/security/advisories)
