# Platform runtime candidates

**Evaluated:** 2026-09-11. **Scope:** HAProxy 3.4.4, Podman and Quadlet
v6.1.1, and systemd-networkd v261.3. These are source evaluations, not MULE
package pins or hardware qualification.

## HAProxy

HAProxy fits the stable local service-ingress role selected by `FML-ADR-031`.
It can forward TCP without terminating the backend protocol and can select a
backend using health checks. Listener ports, administrative sockets, runtime
users and TLS termination are configuration choices; the source does not
impose a MULE port or identity. HAProxy has no application-data store, so its
durable state is its configuration and any deliberately persisted TLS or
runtime-state files.

The evaluated artifact is HAProxy 3.4.4 at commit
`7f03ae65c28605152c7a1a9ba7d9d0bcfb50f8b0` in HAProxy's official 3.4
maintenance repository. The official 3.4 bug page identifies 3.4.4 as the
latest maintenance release on 2026-08-27 and warns that 3.4.0 lacks subsequent
fixes. This is why the intake does not use the older tag exposed by the GitHub
mirror. HAProxy uses GPL-2.0-or-later for the core and LGPL-2.1-or-later for
exported headers, with the documented OpenSSL linking exception. The exact
artifact has not been run in the flat-sat.

Adoption here means the role already approved by `FML-ADR-031`; it does not
approve a package version, listener address, port, backend-discovery contract
or TLS policy. Those remain inputs to the deployable compatibility set and the
service-catalog work.

## Podman and Quadlet

Podman and Quadlet fit the rootless service runtime selected by `FML-ADR-029`.
Quadlet is a systemd generator that turns declarative container, volume,
network and related unit files into systemd services. Rootless Podman uses user
namespaces and per-user storage; it does not make a container harmless, and a
privileged device, host mount or API socket can reintroduce host authority.

The evaluated artifact is Podman v6.1.1 at commit
`8303f2e25b675ea7f82099d615c60969aec15870`, released 2026-09-02 under
Apache-2.0. The GitHub repository listed nine advisories on 2026-09-11. The
published runtime ranges place v6.1.1 after the declared fixes for eight; the
workflow advisory `GHSA-34xh-hvp7-r2j7` declares no version range and therefore
cannot be dismissed by comparing versions. No MULE image or container catalog
has been exercised on this exact release.

Adoption does not select container images. Every image still needs an immutable
digest, license and dependency review, least-privilege mounts and capabilities,
declared persistent paths, an update/rollback procedure and flat-sat coverage.

## systemd-networkd

systemd-networkd fits the single link-owner decision in `FML-ADR-059`. It owns
link creation, addressing and declarative attachment to `batman-adv` while
`wpa_supplicant` and `hostapd` retain wireless association. Its configuration
is durable under the systemd network configuration directories; acquired
leases and operational state are runtime state rather than an application
database.

The evaluated artifact is systemd v261.3 at commit
`3255daee1572366b74fe92f002a3d60ecbb27103`, dated 2026-09-10. The project uses
LGPL-2.1-or-later for most systemd code with GPL-2.0-or-later and other licenses
for identified files. The repository advisory endpoint listed 15 advisories on
2026-09-11; their published fixed-version fields place v261.3 after every
listed fix, including the v261.2 fixes for the newest `systemd-homed` and
`systemd-machined` entries. This comparison does not replace distribution
security tracking.

The exact release has not been used in the flat-sat. Existing configuration
and simulated mesh evidence exercise the selected ownership model on other
versions and do not qualify v261.3 or any driver behavior.

## Shared gaps and exit strategy

No evaluated source tag is a package pin. `TBR-LINUX-01` must select the kernel
and userland before the image manifest can bind these components to exact
distribution builds. Promotion then needs a clean image build, configuration
validation, least-privilege inspection, service failover tests, reboot and
rollback evidence.

HAProxy is isolated behind stable DNS and ingress configuration, Podman behind
Quadlet units and the service catalog, and networkd behind generated network
configuration. Those boundaries allow a later implementation change without
changing EUD protocols or mission data.

## Sources

- [HAProxy 3.4.4 source](https://git.haproxy.org/?p=haproxy-3.4.git;a=tree;h=7f03ae65c28605152c7a1a9ba7d9d0bcfb50f8b0)
- [HAProxy license](https://git.haproxy.org/?p=haproxy-3.4.git;a=blob;f=LICENSE;hb=7f03ae65c28605152c7a1a9ba7d9d0bcfb50f8b0)
- [HAProxy 3.4 maintenance status](https://www.haproxy.org/bugs/bugs-3.4.0.html)
- [Pinned Podman overview](https://github.com/containers/podman/blob/8303f2e25b675ea7f82099d615c60969aec15870/README.md)
- [Pinned Podman license](https://github.com/containers/podman/blob/8303f2e25b675ea7f82099d615c60969aec15870/LICENSE)
- [Pinned Quadlet documentation](https://github.com/containers/podman/blob/8303f2e25b675ea7f82099d615c60969aec15870/docs/source/markdown/podman-systemd.unit.5.md)
- [Podman advisories](https://github.com/containers/podman/security/advisories)
- [Pinned networkd manual](https://github.com/systemd/systemd/blob/3255daee1572366b74fe92f002a3d60ecbb27103/man/systemd-networkd.service.xml)
- [Pinned systemd licenses](https://github.com/systemd/systemd/tree/3255daee1572366b74fe92f002a3d60ecbb27103/LICENSES)
- [systemd advisories](https://github.com/systemd/systemd/security/advisories)
