# Inventory

Ansible inventory for MULE host provisioning.

| File | Contents |
| --- | --- |
| `example.yml` | Example inventory. **Every identity in it is fake.** |

## Real inventories are never committed

`example.yml` uses obviously fake hostnames, documentation-range addresses, and
a placeholder user. It exists to show the shape and to give CI something to
parse.

**A real inventory names real nodes, real addresses, and real operators.** That
is a description of a deployment: who participates, how many nodes, and how to
reach them. It is exactly what the publication rule in `SECURITY.md` exists to
keep out of a public repository maintained by the organisation that operates the
system.

Copy `example.yml` to a path under `mission/local/`, which is git-ignored, and
use it from there:

```sh
ansible-playbook -i mission/local/inventory.yml os/ansible/site.yml --check
```

## Addressing

The addresses in `example.yml` are RFC 5737 documentation addresses. They are
not a proposed scheme.

Addressing is **not decided**: address family, whether the prefix is fixed
across deployments or set per deployment in the mission package, and whether
host addresses derive from node identity are all open. See `TBR-NET-01`, which
needs no hardware and is available to any contributor.
