# OSS-01 evidence

This directory records execution and closure evidence for OSS-01, the prior-art
and reuse register.

`execution-card.md` fixes the scope and verification contract.
`2026-09-12-verification.json` retains the independent machine-readable result,
and `closure.md` records why the finding is closed.

The work is documentation and repository-tooling evidence. It cannot establish
hardware behavior.

## Evaluation progress

As of 2026-09-11, all 28 registered candidates have reached `EVALUATED`.
The first nine are Project N.O.M.A.D., OpenMANET firmware, `openmanetd`,
Reticulum, NomadNet, Martin, OpenTAKServer, PyTAK and Meshtastic firmware.
The platform-stack increment adds HAProxy, Podman and Quadlet, batman-adv and
batctl, hostapd, wpa_supplicant, dnsmasq, systemd-networkd, nftables, chrony,
OpenSSH server, Smallstep step-ca and PostgreSQL. The final increment adds
Kiwix, Kolibri, ProtoMaps basemaps, PMTiles, the Tailscale client, and the Morse
Micro Linux driver and firmware.

The register preserves the governing decision state instead of treating an
evaluation as approval. dnsmasq and step-ca remain undecided, and hostapd 2.12
cannot promote with RADIUS enabled because upstream advisory 2026-5 postdates
that tag. Kiwix, Kolibri, Tailscale and both Morse artifacts remain undecided;
ProtoMaps basemaps and PMTiles are retained only as external-provisioning or
format references. `/root/oss_gap02_closure_verifier` independently
authenticated the implementation commit, reproduced the complete no-skip gate,
exercised the focused failures, and re-resolved all 30 immutable Git artifacts.
OSS-01 is `CLOSED`.
