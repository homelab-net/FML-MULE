# Evidence for TBR-TAK-01

**Trade:** Mission-critical state boundary

**Trade file:** `docs/trades/TBR-TAK-01-mission-critical-state-boundary.md`

**Priority:** 9 of 16 (SAD v0.31 section 30.2). **Function owner:** TAK + SRE.
**Named owner:** `TBD-SRR`.

**Current contents:** the analysis half only. This trade remains `OPEN`.

- `2026-08-27-state-classification-analysis.md` -- method, the ten SAD 14.1
  categories classified, and the partition and rejoin behaviour of the durable
  set including its conflict-resolution rule.
- `2026-08-30-opentakserver-state-inventory.md` -- what state exists at all,
  from the shipped models. Classifies nothing by design.
- `2026-08-31-relational-state-decomposed-into-conops-classes.md` -- **all 36
  tables classified** into CONOPS 26.1, 26.2 and 26.3 with a justification each,
  which is the join the first two left undone. It corrects the inventory's
  count and its `packages` mapping, and records that
  `meshtastic_channels` carries a `psk`, so a credential lives inside the
  relational state that `FML-ADR-034` may replicate.

- `2026-08-31-durable-state-outside-the-database.md` -- **outstanding item 2,
  answered.** Durable state lives in three places outside SQL: `config.yml`,
  which holds the password salt and node identity; `ca/`, the certificate
  authority; and `uploads/`. A database high-availability mechanism protects
  none of them. Losing the salt makes every stored password hash unverifiable.

- `2026-08-31-opentakserver-actually-run.md` -- **the first artifact with a
  running server.** No official OTS container image exists to pin, upstream's
  Dockerfile is unpinned at three layers, its chosen Python 3.13 base makes
  `gevent` assert, and the state inventory had **missed the entire
  authentication store**: 41 tables, not 36. `config.yml` holds 12
  secret-bearing keys including MFA secrets, and the CA private key is on disk.

- `2026-08-31-cot-end-to-end-with-pytak.md` -- a connected PyTAK client.
  **OpenTAKServer is three processes and upstream's container runs one**, so a
  container built from upstream's Dockerfile accepts no TAK clients at all.
  A default `administrator` account is created with the password `password`.
  The PLI path works end to end, the EUD self-registers without a certificate,
  and **outstanding item 3 is answered for that path**: the only queue is
  `cot_parser`, non-durable, carrying reconstructable state.

- `2026-08-31-no-durable-queue-holds-anything.md` -- **outstanding item 3,
  closed.** Two PyTAK clients and a GeoChat message: the text reaches the
  database, a chatroom is created with both participants, and RabbitMQ still
  holds exactly one queue, `cot_parser`, non-durable and empty. The durable
  exchanges have no queues bound to them, and an exchange with no queue stores
  nothing. **No durable queue holds a sole copy because no durable queue
  exists.** Caveat: the clients are PyTAK, not ATAK.

- `2026-08-31-different-node-restore.md` -- **outstanding item 4, performed.**
  A database-only backup restored to a replacement host with an empty data
  folder. Every row survived; the ability to use any of it did not. The default
  administrator logs in on the origin and fails on the replacement, because the
  password salt lives in `config.yml`. The replacement **silently generated a
  different certificate authority**. It reports `/api/health` `200` throughout.

- `2026-08-31-mission-api-and-the-header-that-authenticates.md` -- the Mission
  API, run **first** because it was the case most likely to overturn item 3. It
  does not: the `missions` exchange still has no queue bound. Getting there
  found that `X-Ssl-Cert` **authenticates on a certificate alone with no proof
  of possession**, that the CA key opens with the default password, and that
  the API reported failure after creating the mission.

**Items 5 and 6 remain in part**: DataSync content, mission packages,
certificate enrollment through the proper flow, and the cache question, and none of
them is hardware: durable-queue inspection, a different-node restore, the four
workflow tests, and the cache question.

| Artifact | What it is | Status |
| --- | --- | --- |
| `2026-08-27-state-classification-analysis.md` | The ten SAD section 14.1 categories placed into the three CONOPS section 26 classes, with the durable set and its partition and rejoin behaviour | `UNVERIFIED` |

**That artifact does not close this trade**, and says so in its own opening
section. The listed evidence also requires a different-node restore and the
DataSync, mission-package, certificate and map-cache tests, none of which has
been performed. SAD section 14.2 is explicit that support claimed rather than
demonstrated is not acceptance evidence, and a classification derived from
documentation is a claim about what state *is*, not about where an
implementation *puts* it.

Five findings in it are worth a reader's attention before the empirical half
runs, particularly the fifth: at least two members of the durable set appear to
sit outside any plausible SQL backend, which would make database high
availability necessary and not sufficient, and would change the shape of
`TBR-HA-01`.

This directory existed before the work did, deliberately. The closure gate is
written in the trade file before evidence is gathered, so the result cannot be
graded against a standard invented after seeing it.

## What belongs here

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are transcribed from the SAD and are authoritative;
this file does not restate them, so that the two cannot drift apart.

Every artifact follows the naming and recording rules in
`docs/evidence/README.md`:

- `YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`
- Measurements record instrument, date, node, image build, configuration,
  ambient conditions, and who took them.
- Vendor datasheets go in `datasheets/` with a `.SOURCE.md` recording the
  URL, retrieval date, and document revision. Archive them when you cite them;
  vendors delete PDFs. SAD section 34 is the program's external source register.
- Nothing real: no deployment location, member identity, callsign, credential,
  or operational capture. Strip photograph metadata. See `SECURITY.md`.

**Requires hardware:** No. A design and analysis trade, resolvable against documentation, protocol

## Closing

Evidence here is necessary and not sufficient. SAD section 30.2: a TBR closes
only when its listed evidence exists, **the named owner accepts the evidence**,
and the resulting architecture decision is entered into the persistent ADR
register.

Closing a trade whose named owner is still `TBD-SRR` is not possible, because
there is nobody to accept the evidence.
