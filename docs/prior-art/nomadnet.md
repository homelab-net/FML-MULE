# NomadNet

**Evaluated:** 2026-09-10 at release `1.2.0`, commit
`475c0ee2a0388cf8470e7f1e90d5decb67b579ea`. **Verdict:** retain as
pattern-only messaging and offline-content prior art; do not adopt it.

## Fit

NomadNet is a Python terminal client and daemon for encrypted messaging,
store-and-forward delivery, hosted pages and file transfer. It runs on LXMF and
Reticulum and therefore belongs to their separate identity, routing and client
ecosystem rather than the ATAK/TAK and Meshtastic paths selected for MULE.

Its delayed-delivery, page caching and low-bandwidth content patterns bear on
`FML-REQ-013`, `FML-REQ-018` and `FML-REQ-029`. They are useful comparisons, but
deploying NomadNet would require operators and EUDs to use another client and
would depend on the Reticulum implementation whose field-of-use license is
recorded as incompatible in the adjacent Reticulum evaluation.

## Runtime and trust boundary

NomadNet creates or loads a primary cryptographic identity and stores messages,
attachments, conversations, directories, pages, files and caches beneath its
configuration tree. It defaults to `/etc/nomadnetwork` when a configuration is
present there, otherwise XDG configuration, then `~/.nomadnetwork`. Its container
declares the Reticulum and NomadNet trees as persistent volumes.

The optional node can serve executable pages. Pinned runtime source invokes an
executable page directly and passes submitted fields through environment
variables. That feature expands the trust boundary beyond a passive content
server and would require explicit sandbox and authorization work. Reticulum
interfaces determine listening ports and peer access; NomadNet itself does not
declare a conventional IP service port.

## Intake result

- License: the repository license is GPL-3.0. Package metadata incorrectly
  classifies it as MIT. Runtime dependencies include LXMF and the restricted
  Reticulum implementation, so the dependency/license review is incomplete and
  direct reuse is rejected regardless of NomadNet's own GPL terms.
- Maintenance: five releases were published between 2026-04-22 and 2026-05-21;
  later default-branch commits exist. Contributor totals are heavily concentrated
  in one maintainer.
- Platform: Python 3.8 or later; upstream describes desktop Python systems,
  Android through Termux and an Alpine-based OCI image.
- Resources: not measured for a MULE profile.
- Data: configuration, identity, message store, attachments, conversations,
  directory entries, peer settings, hosted pages/files and caches. No complete
  backup or migration contract was identified.
- Security: no repository advisory was published through GitHub's advisory
  endpoint on 2026-09-10. No independent audit or repository SBOM was identified.
- Prototype: not run. The pinned Docker documentation uses mutable tags and host
  networking, so it is not a deployable MULE profile.

## Exit strategy and questions

Keep only the pinned evaluation and pattern notes. Do not package NomadNet,
Reticulum or LXMF. If a future approved scope adds a non-TAK messaging client,
evaluate the complete dependency chain and executable-page isolation before any
prototype. The present question is whether its store-and-forward and page-cache
ideas reveal a missing requirement in the existing upstream TAK/Meshtastic path.

## Sources

- [Pinned README](https://github.com/markqvist/NomadNet/blob/475c0ee2a0388cf8470e7f1e90d5decb67b579ea/README.md)
- [Pinned license](https://github.com/markqvist/NomadNet/blob/475c0ee2a0388cf8470e7f1e90d5decb67b579ea/LICENSE)
- [Pinned package metadata](https://github.com/markqvist/NomadNet/blob/475c0ee2a0388cf8470e7f1e90d5decb67b579ea/setup.py)
- [Pinned container build](https://github.com/markqvist/NomadNet/blob/475c0ee2a0388cf8470e7f1e90d5decb67b579ea/Dockerfile)
- [Pinned application storage](https://github.com/markqvist/NomadNet/blob/475c0ee2a0388cf8470e7f1e90d5decb67b579ea/nomadnet/NomadNetworkApp.py)
- [Pinned node execution path](https://github.com/markqvist/NomadNet/blob/475c0ee2a0388cf8470e7f1e90d5decb67b579ea/nomadnet/Node.py)
- [Release history](https://github.com/markqvist/NomadNet/releases)
- [Contributor summary](https://api.github.com/repos/markqvist/NomadNet/contributors)
- [Repository security advisories](https://github.com/markqvist/NomadNet/security/advisories)
