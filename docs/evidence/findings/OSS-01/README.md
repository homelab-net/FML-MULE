# OSS-01 evidence

This directory records execution and eventual closure evidence for OSS-01, the
prior-art and reuse register.

`execution-card.md` fixes the scope and verification contract before the
registry implementation begins. A closure packet and retained machine-readable
results will be added only after the complete candidate corpus is evaluated and
an independent P0 reviewer reproduces the acceptance checks.

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
format references. OSS-01 remains `IMPLEMENTED` until an independent P0
reviewer reproduces the acceptance checks and the closure packet is complete.
