# Project N.O.M.A.D

**Evaluated:** 2026-09-10 at release `v1.34.1`, commit
`f8e40fbd01f4ce0e6bc4cc3e37167b4bf4065028`. **Verdict:** retain as
pattern-only prior art for offline-content selection and management; do not
adopt its management stack.

## Fit

Project N.O.M.A.D. is an offline-first browser application that orchestrates
containers for Kiwix, Kolibri, ProtoMaps, local AI and other content services.
That service catalog overlaps the MULE's offline-content questions, especially
`FML-REQ-016` and `FML-REQ-018`.

The deployment material in the pinned repository artifact does not fit the
selected MULE execution and security model:

- upstream states that the application has no authentication and is not meant
  to be exposed directly to the Internet;
- the administrator, updater and log-viewer containers mount the host Docker
  socket, while the updater also writes `/opt/project-nomad`;
- the supplied compose file publishes the administrator on port 8080 and the
  log viewer on port 9999;
- its compose images use mutable tags such as `latest`, while this repository
  requires OCI images by immutable digest; and
- its pinned installer downloads start, stop and update helper scripts from
  `refs/heads/main`, so running that installer does not reproduce only the
  pinned release; and
- the installer requires root privileges and writes generated application and
  database secrets into the compose configuration.

Those are properties of the inspected release, not a claim that the project is
unsafe for its intended isolated-home use. They make the management stack a
poor fit for a field node carrying controlled mission services.

## Reusable work

The useful work is the content acquisition and lifecycle pattern: a locally
served catalog, explicit offline downloads, and persistent stores for ZIM and
PMTiles material. FML evaluates the underlying Kiwix, Kolibri, ProtoMaps and
PMTiles projects independently, so adopting this orchestration layer would add
a second service controller rather than remove one.

## Intake result

- License: Apache-2.0 for the repository; bundled dependency review remains
  pending.
- Maintenance: current releases and commits were present at evaluation time.
  GitHub's contributor summary shows meaningful work from two human accounts,
  with lower-volume contributions beyond them.
- Resources: not measured. Upstream hardware guidance is not treated as a MULE
  measurement.
- Security: no repository security advisory was published through GitHub's
  advisory endpoint on 2026-09-10. No independent audit or repository SBOM was
  identified in the pinned artifact.
- Prototype: not run. A deployment would exercise privileged host control and
  mutable images without answering a selected MULE trade.

## Exit strategy and questions

Keep this document as the reference. Source any selected content service from
its canonical upstream and retain no Project N.O.M.A.D. runtime dependency.
The remaining question is which individually evaluated offline-content
components satisfy the MULE service trades.

## Sources

- [Pinned README](https://github.com/Crosstalk-Solutions/project-nomad/blob/f8e40fbd01f4ce0e6bc4cc3e37167b4bf4065028/README.md)
- [Pinned compose file](https://github.com/Crosstalk-Solutions/project-nomad/blob/f8e40fbd01f4ce0e6bc4cc3e37167b4bf4065028/install/management_compose.yaml)
- [Pinned installer](https://github.com/Crosstalk-Solutions/project-nomad/blob/f8e40fbd01f4ce0e6bc4cc3e37167b4bf4065028/install/install_nomad.sh)
- [Pinned updater](https://github.com/Crosstalk-Solutions/project-nomad/blob/f8e40fbd01f4ce0e6bc4cc3e37167b4bf4065028/install/update_nomad.sh)
- [Release history](https://github.com/Crosstalk-Solutions/project-nomad/releases)
- [Contributor summary](https://api.github.com/repos/Crosstalk-Solutions/project-nomad/contributors)
- [Repository security advisories](https://github.com/Crosstalk-Solutions/project-nomad/security/advisories)
