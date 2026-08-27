# Role: common

Base host configuration applied to every MULE node, regardless of hardware
block or region.

**Status: skeleton. This role does almost nothing, deliberately.**

## Why it is nearly empty

Most of what a `common` role would normally do is either not decided or belongs
in the image rather than here:

- **Package installation** belongs in the image, pinned in
  `os/image/manifest/`. Installing packages from a role reintroduces the drift
  that pinning exists to prevent. See `os/README.md`.
- **Radio configuration** waits on `TBR-LINUX-01`, `TBR-RF-01`, `TBR-RF-02`
  and `TBR-RF-03`, and comes from a region profile rather than from this role.
- **Firewall policy** waits on `TBR-NET-01` and `TBR-TAK-01`.
- **Identity and trust material** waits on `TBR-SEC-01`, and none of it is ever
  committed to this repository in any case.
- **Service deployment** is Quadlet units from `services/quadlets/`, not
  Ansible tasks.

Filling this role with plausible-looking tasks now would create work that has
to be undone when those trades close.

## What belongs here eventually

Host configuration that is genuinely common across every block and region and
that legitimately cannot be baked into the image: node identity assignment,
time configuration per `FML-ADR-042`, journal and logging policy, and the
resource reservation that keeps the network plane alive under service-plane
load per `TBR-COMP-01`.

## Layout

Ansible fixes these directory names; they are not a choice this program made,
and they carry no `README.md` of their own because the tooling expects exactly
this shape.

| Directory | What Ansible looks for there |
| --- | --- |
| `tasks/` | The work the role performs. `main.yml` is the entry point. |
| `defaults/` | Variables the role defines and a playbook may override. Lowest precedence, so a region profile or mission package always wins. |
| `handlers/` | Actions triggered by a task reporting a change, such as restarting a unit. |
| `meta/` | Role metadata and dependencies on other roles. |

## Conventions

- Idempotent. A second run changes nothing.
- Tasks named in sentence case, describing what they achieve.
- `ansible-lint` and `yamllint` clean.
- No secrets, no region-specific values, no invented values.
