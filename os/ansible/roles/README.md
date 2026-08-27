# Roles

Ansible roles for MULE host provisioning.

| Role | Purpose | State |
| --- | --- | --- |
| `common/` | Base host configuration applied to every node. | Skeleton. Does almost nothing, deliberately. |

`common/` is the only role. Radio, service and identity roles come later and
wait on the trades their configuration depends on; see `roles/common/README.md`
for why filling a role with plausible-looking tasks now would create work that
has to be undone.

## Adding a role

- Standard Ansible layout: `tasks/`, `defaults/`, `handlers/`, `meta/`, and
  `templates/` or `files/` where needed. Those directory names are fixed by
  Ansible and mean what Ansible says they mean.
- A `README.md` at the role root stating what the role does, what it
  deliberately does not do, and which trades it waits on.
- **Idempotent.** A second run changes nothing. A role that reports changes on
  every run cannot be used to detect drift, which is most of what it is for.
- `ansible-lint` and `yamllint` clean, and passes `--check`.
- **No secrets, no region-specific values, no invented values.** Frequencies,
  channels and power come from `regions/<region-id>/profile.yml`.

## Image or role

Before adding a task, ask whether it belongs in the image instead. Configuration
baked into the image is reproducible and covered by the compatibility set
version a node reports; configuration applied by a role is state that can drift,
and a node that has drifted from its set version is undiagnosable from the
version alone.

**The program's bias is toward baking.** See `os/ansible/README.md`.
