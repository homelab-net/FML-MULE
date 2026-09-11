# Mesh and local-network candidates

**Evaluated:** 2026-09-11. **Scope:** batman-adv and batctl v2026.3,
hostapd and wpa_supplicant 2.12, dnsmasq 2.93, and nftables 1.1.7. These
source evaluations do not select a kernel, radio, channel, interface name,
address, port exposure or package build.

## batman-adv and batctl

`batman-adv` and `batctl` fit the layer-2 mesh selected by `FML-ADR-053` and the
ownership boundary selected by `FML-ADR-059`. The kernel module carries mesh
frames and exposes its control surface through generic netlink and sysfs;
`batctl` is the matching user-space inspection and control client. It does not
open an application TCP or UDP service. Changing mesh state requires root or
the corresponding network capability.

The two evaluated artifacts are the paired v2026.3 releases: batman-adv commit
`f38d7c3263ab0ba6c08b232eed55f63a6b8a6775` and batctl commit
`9e098cb2bcd40e367f91f1a3c5379ea4d4e0f9da`, both dated 2026-08-31. Their
principal license is GPL-2.0, with identified Linux-syscall-note and MIT files.
Compatibility with the eventual MULE kernel and distribution package set is
not established. Existing flat-sat evidence used other module versions and
remains `SIMULATED`.

The 2026 NVD keyword inventory returned 47 records mentioning batman-adv. Of
those, 46 describe batman-adv defects; their fix subjects all appear in the
v2026.0 through v2026.3 changelog, so the evaluated out-of-tree v2026.3 source
contains those fixes. `CVE-2026-74310` is a vhost/net defect that names
batman-adv fragmentation as a triggering example, not a defect fixed in the
out-of-tree module. This conclusion does not transfer to an eventual Debian
kernel package: `TBR-LINUX-01` must identify its in-tree source and security
backports independently.

Adoption is limited to the already selected mechanism. `TBR-LINUX-01` still
owns the exact kernel/module/tool set, and real radios must demonstrate mesh
formation, reboot, recovery and the selected BATMAN-IV settings.

## hostapd and wpa_supplicant

The two programs share the hostap source tree. `hostapd` owns EUD access-point
association and its integrated EAP server is the preferred initial admission
path in `FML-ADR-038`. `wpa_supplicant` owns station and 802.11s mesh
association under `FML-ADR-059`. Neither replaces `systemd-networkd` as link
owner.

The evaluated artifact is hostap 2.12 at commit
`831364bf02710ad09c2f27d3efa92abeeb5634c0`, dated 2026-08-07 under the BSD
three-clause license. Both daemons use driver control interfaces and local
control sockets. Their network ports depend on the selected AP/EAP/RADIUS and
management configuration. Configuration may contain SAE, PSK, EAP, RADIUS and
private-key material and therefore belongs in the protected mission-profile
path, never in this repository.

The exact release has not been exercised with mac80211_hwsim or MULE hardware.
Driver support for the selected HaLow device, EAP-TLS admission, fail-closed
behavior and control-socket permissions remain promotion gates.

The exact hostapd artifact is not promotable with a RADIUS-enabled profile.
Upstream advisory 2026-5 was published ten days after 2.12 and states that all
hostapd versions with RADIUS enabled at runtime are vulnerable to incomplete
Message-Authenticator validation. Upstream directs users to 2.12.1, 2.13 or
newer once available, or to commit
`aa02cfa569477f67f3915c8b9a83d1a7ca93693d`. The 2.12 tag already contains the
fixes named by advisories 2026-1 through 2026-4; the registry records which
program each applies to. The next compatibility-set candidate must use a fixed
hostapd artifact and exercise malformed RADIUS messages when that path is
enabled.

## dnsmasq

dnsmasq combines local DNS and DHCP and matches the small-node pattern already
represented by `os/config/dnsmasq.conf.template`. When enabled, DNS normally
uses TCP and UDP 53, DHCPv4 uses UDP 67/68, and optional DHCPv6 or TFTP adds its
own configured listeners. Lease state can be persisted; names, addresses,
upstream resolvers and credentials are deployment inputs.

The evaluated artifact is dnsmasq 2.93 at commit
`3ff66da573a77c8783deca10ec8c6bba07cd85e6`, dated 2026-06-04. Upstream permits
redistribution under GPL-2.0 or GPL-3.0. The official CVE directory records six
2026 fixes that entered 2.92rel2 and the 2.93 release line. This source review
did not establish a complete dependency SBOM.

The architecture selects stable local DNS, not dnsmasq specifically. Reuse
therefore remains undecided until `GAP-02` and the deployable service/network
catalog approve the exact DNS/DHCP behavior and security profile.

## nftables

nftables fits the shared-kernel isolation and forwarding decisions in
`FML-ADR-030` and `FML-ADR-068`. It programs the kernel packet filter through
netlink and does not itself expose a network listener. Loading or changing a
ruleset requires root or `CAP_NET_ADMIN`; the durable input is the generated
ruleset, while counters and connection tracking are runtime state.

The evaluated artifact is nftables 1.1.7 at commit
`8c2f60661c9e8e85869f82db25961b45a8d07554`, dated 2026-09-01 and licensed
GPL-2.0. It has not been run against the MULE template. Promotion must test the
exact userspace/kernel combination, default-deny segmentation, established
flows, WAN forwarding, failure behavior and rollback without granting mission
services direct network authority.

## Shared gaps and exit strategy

The selected roles are separated by standard Linux interfaces: networkd owns
links, hostapd and wpa_supplicant own association, batman-adv owns mesh
forwarding, dnsmasq or an approved equivalent supplies DNS/DHCP, and nftables
owns packet policy. Keeping those seams allows one component to be replaced
without creating a custom over-the-air protocol.

No exact source release is a MULE package pin. The compatibility-set decision,
distribution security support, SBOM, resource measurements and hardware tests
remain open.

## Sources

- [Pinned batman-adv source](https://git.open-mesh.org/batman-adv.git/tree/?id=f38d7c3263ab0ba6c08b232eed55f63a6b8a6775)
- [Pinned batctl source](https://git.open-mesh.org/batctl.git/tree/?id=9e098cb2bcd40e367f91f1a3c5379ea4d4e0f9da)
- [batman-adv documentation](https://www.open-mesh.org/projects/batman-adv/wiki)
- [NVD batman-adv search](https://nvd.nist.gov/vuln/search/results?query=batman-adv)
- [Linux CVE records](https://git.kernel.org/pub/scm/linux/security/vulns.git/)
- [Pinned hostap license](https://w1.fi/cgit/hostap/tree/COPYING?id=831364bf02710ad09c2f27d3efa92abeeb5634c0)
- [Pinned hostapd documentation](https://w1.fi/cgit/hostap/tree/hostapd/README?id=831364bf02710ad09c2f27d3efa92abeeb5634c0)
- [Pinned wpa_supplicant documentation](https://w1.fi/cgit/hostap/tree/wpa_supplicant/README?id=831364bf02710ad09c2f27d3efa92abeeb5634c0)
- [Hostap security advisories](https://w1.fi/security/)
- [Hostapd RADIUS advisory 2026-5](https://w1.fi/security/2026-5/incomplete-radius-message-authenticator-attribute-validation-in-hostapd.txt)
- [Pinned dnsmasq source](https://thekelleys.org.uk/gitweb/?p=dnsmasq.git;a=tree;h=3ff66da573a77c8783deca10ec8c6bba07cd85e6)
- [dnsmasq CVE fixes](https://thekelleys.org.uk/dnsmasq/CVE/)
- [Pinned nftables source](https://git.netfilter.org/nftables/tree/?id=8c2f60661c9e8e85869f82db25961b45a8d07554)
- [nftables documentation](https://netfilter.org/projects/nftables/)
