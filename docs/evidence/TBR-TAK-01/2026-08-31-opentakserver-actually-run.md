# OpenTAKServer, actually run

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. A running instance on a development
machine, in containers, with no MULE hardware and no client connected.

## What this is, and what it is not

Every prior artifact under this trade was read from schema or source, and each
said so. This is the first with a **running** server, which SAD section 14.2
demands: "database support claimed by an ORM is not sufficient acceptance
evidence".

**It is not a deployment.** `services/catalog/` is empty by decision,
`services/quadlets/` holds no service definition, and `services/tak/` records
that nothing is deployed pending this trade. No Quadlet and no catalog entry
were written. The container recipe lives in the scratch directory, not in the
repository, because a file appearing in `quadlets/` is precisely what the
catalog exists to prevent.

## Configuration

| Item | Value |
| --- | --- |
| Runtime | Podman 5.4.2, `FML-ADR-029`'s selected runtime |
| Rootless | **No.** This environment runs as uid 0, which is a deviation from `FML-ADR-029`'s field pattern and is recorded rather than hidden. |
| OpenTAKServer | 1.7.13 from PyPI |
| Base image | `docker.io/library/python@sha256:de8ba566572ebcb35cbd10e03f5f351cad00a0d0d50a11e084f1a0fd24a0c41a` |
| PostgreSQL | `docker.io/library/postgres@sha256:485935f94cc7165afa896978809c37b592dc07f0a37d2c8f645f12412d0212c8` |
| RabbitMQ | `docker.io/library/rabbitmq@sha256:9cfb7e92ae7d296aec4d1ae799e431209f7ed57d55f9c929d95667d0ccf1c920` |

Every image is pinned by digest, per `FML-ADR-029`. That mattered, for the
reason below.

## Finding 1: there is no OpenTAKServer image to pin

`FML-ADR-029` requires OCI images "by immutable digest for field releases, never
by tag". **No official OpenTAKServer image exists.**

- Docker Hub search returns nine `opentakserver` repositories. All are
  third-party, all have zero stars, and none belongs to the upstream author.
- No image is published under the upstream project on GHCR.
- Upstream's `README.md` names no container registry.

Upstream ships a `Dockerfile` and publishes no image from it. So the program's
options are to build and host its own image, run OpenTAKServer outside a
container, or depend on an anonymous third-party build. **The third is not
compatible with `FML-ADR-029`.**

## Finding 2: upstream's Dockerfile is unpinned at three layers

```dockerfile
FROM python:3.13
RUN apt update && apt install ffmpeg -y
# TODO: Install from PyPI
RUN pip install git+https://github.com/brian7704/OpenTAKServer.git
```

A floating base tag, unpinned apt packages, and **the application installed from
git master with no ref**. Two builds a day apart can contain different software,
and upstream's own comment marks the last as a known shortcut.

The image used here was therefore built to this program's rules instead: base by
digest, application by pinned PyPI release.

## Finding 3: upstream's chosen base breaks its own runtime

`gevent` in the shipped dependency set asserts that it is not running on Python
3.13:

```text
File "gevent/threading.py", line 397, in after_fork_in_child
    assert sys.version_info[:2] < (3, 13)
AssertionError:
```

Upstream's Dockerfile selects `FROM python:3.13`. The assertion fires on every
fork, repeatedly, in the logs.

**The server nonetheless serves**: `/api/health` returns `200`. So this is
noise rather than failure at present, and it is exactly the kind of noise that
hides a real fault later.

## Finding 4: the state inventory missed the authentication store

The 2026-08-30 inventory and the 2026-08-31 decomposition both enumerated
tables by matching `__tablename__` literals in `opentakserver/models/*.py`, and
both reported **36**.

A running PostgreSQL holds **41**:

| Table | Rows after first start | Why it was missed |
| --- | --- | --- |
| `user` | 1 | Name comes from a Flask-Security `fsqla` mixin, not a `__tablename__` literal |
| `role` | 2 | Same |
| `roles_users` | 1 | Same |
| `web_authn` | 0 | Same |
| `alembic_version` | 1 | Migration marker, created by Alembic |

**The four missed application tables are the entire authentication and
authorisation store**, which is the most security-critical CONOPS 26.1 state in
the system. A method that enumerates literals in a models directory misses any
table whose name a library supplies, and here it missed the user accounts.

Corrected classification: `user`, `role`, `roles_users` and `web_authn` are
**26.1**, common trust and configuration. `alembic_version` is **26.1** as well
-- a restore whose schema version disagrees with the code is not a working
restore.

**Nothing was missing from the other direction.** All 36 previously classified
tables exist in PostgreSQL.

## Finding 5: what the running server writes outside the database

Confirming and extending `2026-08-31-durable-state-outside-the-database.md`,
which predicted three locations from source. There are more:

```text
/data/config.yml
/data/ca/          ca-do-not-share.key, ca.pem, ca-trusted.pem,
                   truststore-root.p12, ca.crl, crl_index.txt, ca_config.cfg
/data/uploads/
/data/logs/        opentakserver.log, opentakserver.log.<date>
/data/icons.sqlite
```

**`config.yml` holds 143 keys, of which 12 bear secrets**, named here without
their values: `SECRET_KEY`, `SECURITY_PASSWORD_SALT`, `SECURITY_TOTP_SECRETS`,
`OTS_CA_PASSWORD`, `OTS_RABBITMQ_PASSWORD`, `OTS_MEDIAMTX_TOKEN`,
`OTS_TAK_GOV_ACCESS_TOKEN`, `OTS_TAK_GOV_REFRESH_TOKEN`, `MAIL_PASSWORD`,
`LDAP_BIND_USER_PASSWORD`, and two password-policy settings that match the
pattern without being secrets.

`SECURITY_TOTP_SECRETS` was not anticipated: **multi-factor authentication
secrets are in this file too.** `OTS_NODE_ID` is present and 32 characters, as
predicted.

**The certificate authority's private key is on disk**, and upstream names it
`ca-do-not-share.key`. A `.crl` and a CRL index sit beside it, which is the
revocation state whose loss the 2026-08-27 analysis said "fails open".

`icons.sqlite` is a **seed file, not a live second store**: PostgreSQL holds
3743 rows in `icons` after first start, and the SQLite file holds the same
shipped set. It is reconstructable from the package.

## Finding 6: an input to outstanding item 3, not an answer

RabbitMQ declares eight exchanges, six of them durable:

```text
groups      topic    durable      dms        direct   durable
firehose    fanout   durable      missions   topic    durable
cot_parser  direct   durable      chatrooms  direct   durable
flask-socketio  fanout  NOT durable
```

**No queues exist**, because queues are created per connected client and none
was connected. So whether a durable queue ever holds the sole copy of a
mission-critical item is still open, and answering it requires a client, which
is outstanding item 5.

That `dms` and `chatrooms` are durable exchanges is the part to carry forward:
direct messages and chat are the traffic most likely to exist only in transit.

## What this does not establish

**No client connected.** No ATAK, iTAK or WinTAK, and no PyTAK. Outstanding
items 4, 5 and 6 -- the different-node restore, the four workflow tests, and the
cache question -- all need one and none was performed.

**Not rootless**, which `FML-ADR-029` requires in the field.

**Nothing about compute cost.** No memory or CPU measurement was taken;
`TBR-COMP-01` needs that and this artifact does not supply it.

**One start, on one machine, with an empty database.** Nothing here observed
behaviour under load, over time, or after a restart.
