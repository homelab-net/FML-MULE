# Provisioning

Ansible roles that provision a node's host configuration on top of the image
produced by `os/image/`.

**Nothing here has been run against real hardware.** The role skeleton exists;
it does almost nothing, on purpose.

## The rule

**Provisioning shall be reproducible with no undocumented manual state.**

If a node needs something done to it, the thing that does it lives here. Not in
a shell history, not in a note, not in the memory of the person who built the
first node. A node that works because someone once ran a command nobody
recorded is a node nobody can rebuild, and it is the normal outcome for a
volunteer hardware project.

Two tests for whether this rule is being followed:

1. Could a second person produce an identical node from this repository alone?
   That is the cold start drill in `docs/verification/`.
2. If every node were lost, could the fleet be rebuilt? That is the same
   question with the stakes made obvious.

## Image or Ansible

The boundary between what is baked into the image and what is applied by
Ansible is `TBD`, and it is a real decision rather than an implementation
detail.

- **Baked into the image:** reproducible, requires a promotion to change, and
  is covered by the compatibility set version a node reports.
- **Applied by Ansible:** flexible, and is state that can drift. A node whose
  configuration has drifted from its set version is undiagnosable from the
  version alone.

**The program's bias is toward baking**, because drift is invisible. Where a
role does something that could have been baked, the reason belongs in the
role's README.

## Structure

```text
ansible/
  README.md
  ansible.cfg
  site.yml                  entry point
  inventory/
    example.yml             example inventory, fake identities only
  roles/
    common/                 base host configuration
      tasks/main.yml
      defaults/main.yml
      handlers/main.yml
      meta/main.yml
      README.md
```

`common/` is the only role. Radio, service and identity roles come later, and
they wait on the trades their configuration depends on.

## Running

```sh
ansible-playbook -i inventory/example.yml site.yml --check
```

`--check` runs in CI as a minimum bar. It confirms the playbook parses and the
tasks are well-formed. It does not confirm anything works: **CI has no radios,
no battery, and no enclosure.** See `test/README.md`.

## Conventions

- `ansible-lint` clean, `yamllint` clean. Both run in CI.
- Tasks are named, in sentence case, describing what they achieve.
- **Idempotent.** A second run changes nothing. A role that reports changes on
  every run cannot be used to detect drift, which is most of what it is for.
- **No secrets in this repository.** No key, certificate, credential, real
  callsign, real member identity, or real deployment location, including in the
  example inventory. See `SECURITY.md`.
- **No region-specific values.** Frequencies, channels and power come from
  `regions/<region-id>/profile.yml`. See `os/config/README.md`.
- **No invented values.** Unknown is `TBD` with the trade that will decide it.

## Poor connectivity

Builders will be on constrained connections. Prefer roles that work against a
local package cache and that do not require reaching a dozen upstream hosts.
See `os/README.md`.
