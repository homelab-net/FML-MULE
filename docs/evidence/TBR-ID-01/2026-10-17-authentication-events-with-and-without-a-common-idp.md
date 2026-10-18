# Authentication events with and without a common identity provider

**Trade:** `TBR-ID-01`.
**Date:** 2026-10-17.
**Produced by:** written analysis against the controlling documents, plus the
offline demonstration recorded beside it in
`2026-10-17-offline-client-certificate-login-fakes.md`. No EUD, no browser, and
no MULE hardware.
**Status of this artifact:** `UNVERIFIED`. It is reasoning, not a result. The
counts below are derived, not observed on a phone.

**It does not close the trade.** The closure gate requires a decision recorded
in the ADR register, the role and scope workflow documented end to end, and
offline login demonstrated **for the selected approach**. Nothing is selected
here. An artifact's presence is not owner acceptance.

## The question, exactly

The trade file asks one thing: *"Is a common browser-service IdP required
beyond native app RBAC?"* ITEP-C01 item 5 turns that into a procedure: *"Count
authentication events with and without one."* The Closure evidence adds three
more: offline login with no WAN, the provisioning burden on the Communications
and Identity Management function per user per mission, and the behaviour when
time is not credible. This file covers all four. The fourth is also
demonstrated, against fakes, in the companion artifact.

**What this does not answer.** Three documents attribute to `TBR-ID-01`
questions its trade file does not ask and its closure gate does not cover. See
finding 6.

## Definitions

An **authentication event** is an occasion on which an operator has to act to
prove who they are. Three kinds are counted separately, because they cost
different things in gloves and darkness (the trade's own framing):

- **typed** -- a username and password, or a code;
- **selection** -- a tap to choose a credential the device already holds, such
  as a browser's client-certificate picker;
- **zero-touch** -- a credential presented with no operator action.

A **browser service that needs identity** is one whose behaviour depends on
who is asking: it attributes an action to a person, or it answers differently
by role or team scope. A service that gives every admitted user the same thing
needs network admission and nothing more. CONOPS section 49 opens with
*"Authenticated EUD users may access approved browser applications"*, and
admission to the operational WLAN is already an authentication: individually
identifiable, revocable and time-bounded under CONOPS section 13 and
`FML-ADR-038`.

## The catalog the program actually fields

The trade says doing nothing may be sufficient *"for the service catalog the
program actually fields"*. That catalog is `services/catalog/catalog.yml`
(`FML-ADR-078`), and it has two entries.

| Entry | State | How it authenticates today | Who uses its browser surface |
| --- | --- | --- | --- |
| `martin` | `enabled: true` | Not at all. The Quadlet publishes only `127.0.0.1:3000`, and `services/map/README.md` leaves *"whether the endpoint is authenticated and how"* to ingress. | Every admitted EUD, identically |
| `opentakserver` | `enabled: false` | Its own username and password (`/api/login`), and HTTP Basic for certificate enrollment; both measured in `docs/evidence/TBR-TAK-01/` | The TAK Administrator (CONOPS 7.5) |

Map tiles are the same for every admitted user, so `martin` needs no identity.
ATAK reaching OpenTAKServer is TAK authorization, the fifth of CONOPS section
13's six separations, and not a browser service.

**So for the fielded catalog the answer is no.** One role uses one
browser service that has its own login. A provider shared by one service is not
common to anything. This is the trade's "doing nothing" option, and against
today's catalog it is not a compromise.

That answer is cheap and fragile: it lasts exactly as long as the catalog does.
The rest of this file answers for the catalog CONOPS section 49 describes.

## The planning case: CONOPS section 49

Section 49 lists nine classes of browser application and says *"Exact software
products are downstream selections."* Classifying each by whether it needs
identity:

| Class | Needs identity? | Why |
| --- | --- | --- |
| group and team messaging | yes | a message has a sender; team scope |
| field portal | yes | *"Authorized services appear"* (CONOPS 66, 82) differs by role |
| files | yes | team scope, CONOPS 7.2 |
| maps | no | the same for every admitted user, as `martin` is today |
| mission reference material | no | CONOPS 7.1 gives it to every Unit Member |
| reporting | yes | a report is attributed |
| logistics and status tools | yes | team scope; a Team Lead's expanded status, CONOPS 7.2 |
| approved sensors | yes | a task names *"the sensor, the duration, and the team scope"*, CONOPS 49 |
| approved AI/RAG | depends | yes if it keeps per-user history; the product is unselected |

**k = 6** services need identity, 7 if AI/RAG keeps history. The counts below
use k = 6. CONOPS section 6 plans **4 to 8** authenticated EUD users per MULE.

## Three options

The trade names two axes: whether a common provider is introduced, and if so
whether it is an existing open-source project or an application-native shared
session. A third option exists that neither axis names, and it is the one the
architecture has already half-built.

- **A, per-application login.** No common provider. Each service keeps its own
  accounts and its own native RBAC (`FML-ADR-037`).
- **B, a common identity provider.** An OIDC or SAML provider on the node; each
  service delegates login to it and keeps native RBAC over the claims it
  returns. No product is named, deliberately.
- **C, ingress client-certificate authentication.** No provider service. The
  `FML-ADR-031` ingress terminates TLS, requires a client certificate chaining
  to the mission authority (`FML-ADR-036`), checks revocation material the
  Mission Trust Service distributes (`FML-ADR-047`), and **sets** the
  authenticated principal on the request. Each service keeps native RBAC,
  reading role and scope from signed role data rather than from the
  certificate (SAD section 16.4; the same path `FML-ADR-087` already assigns
  to the roster).

C is not a new invention so much as an assembly. `services/ingress/README.md`
already records that *"the reverse proxy authenticates"*, and why the proxy
*"shall SET the header, never forward one"*.

## Authentication events per operator

Six situations, each from the operator's side.

| Situation | A, per-app | B, common IdP | C, ingress certificate |
| --- | --- | --- | --- |
| Mission start, first use of all six | **6 typed** | **1 typed**, then redirects that ask nothing | **0 typed**; selection prompts unmeasured, 0 to 6 |
| Node reboots (the trade's case) | 0 to 6 typed, by each product's session persistence | 0 or 1 typed, by the provider's session persistence | **0**: no session to lose |
| Services now come from another MULE | up to 6 typed, and only where the account exists | 1 typed per independent provider; 0 only if provider state is replicated | **0**, demonstrated against fakes |
| EUD replaced (CONOPS 16) | 6 typed after reprovisioning | 1 typed after reprovisioning | 0 typed after reprovisioning; selections as at start |
| Credential renewed | none forced | none forced | 0 at the services; the renewal itself is provisioning, below |
| Node time not credible | logins proceed; see finding 4 | one place can be gated; six still validate tokens | refused at one gate, demonstrated |

**A Unit Member's mission, with one move between MULEs and no reboot:** A is up
to 12 typed events, B is 1 or 2, C is 0 typed plus an unmeasured number of
selections.

The cell that decides between B and C is the one marked unmeasured: whether a
phone's browser presents a client certificate silently, asks once per service,
or asks every time. That is the measurement this artifact cannot make. See
finding 5.

## Provisioning burden per user per mission

For the Communications and Identity Management function (CONOPS 7.6), with N
users and M nodes holding service state.

| | A, per-app | B, common IdP | C, ingress certificate |
| --- | --- | --- | --- |
| Identity records created | up to N x 6 x M | N per provider instance: N x M, or N if replicated | **N**, the credential `FML-ADR-038` admission already issues; 2N if admission and browser identity are kept apart (finding 5) |
| Secrets the user has to hold | 6 passwords, or 1 reused six times | 1 password | none to remember; one credential installed on the device |
| Role and scope entries | N x 6, one per product's native RBAC | N in the provider, plus 6 claim mappings per mission | N rows of signed role data, plus 6 header mappings per mission |
| Places to revoke one user (CONOPS 17) | 6 x M | M, or 1 if replicated | **1** signed record, the same one that removes WLAN admission |
| Recurring work | none forced | none forced | one install per device per renewal, unmeasured |

Illustration only, N = 8 and M = 2: A creates up to 96 account records and has
12 places to revoke each person; B creates 8 to 16 and has 1 or 2; C creates 8,
which admission requires anyway, and has 1.

**`FML-ADR-037` excludes per-application GUI state** as a way to provision
native RBAC: it qualifies *"only if it can be provisioned and reviewed
reproducibly"*. Under A, six products' account stores therefore all need
provisioning from the mission configuration package (CONOPS 19), six
integrations rather than one. That is the per-application burden the closure
gate asks to have stated *"so the identity function knows what it is signing
up for"*.

## Findings

### 1. For the catalog the program fields, no provider is required

Shown above. The decision only becomes real when a second identity-needing
browser service is catalogued.

### 2. A provider would be an S0 service

CONOPS 9.1 lists **authentication** among S0 core node services, and *"S0
functions shall remain active whenever the node is operational."* Under B, the
provider is in the authentication path of every identity-needing service, so it
inherits S0. That makes it a component that has to start before every service it
fronts, survive every reboot, run offline, and fit the budget beside a service
plane already measured at about 650 MB resident at idle, dominated by
OpenTAKServer (`docs/evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md`,
`SIMULATED`, x86). No provider was measured here. Under `TBR-COMP-01` one would
have to be.

B also puts a token-signing key on every node that runs a provider. A node is
expected to be captured (`THREAT_MODEL.md`), and a captured signing key mints
tokens for everything that trusts it. Per-node keys contain that, and are why B
needs a typed login after every move between MULEs unless provider state is
replicated, which is a `TBR-HA-01`-class problem. `TBR-TAK-01` measured the
same shape in OpenTAKServer's defaults: the thing that should be per-node was
shared, and the trust that should be shared was per-node.

### 3. C reuses what four decisions already commit to

C adds no service. It uses the `FML-ADR-038` client credential, the
`FML-ADR-047` revocation material, the `FML-ADR-087` signed role state and the
`FML-ADR-031` proxy. The demonstration exercised the properties that matter
against fakes, with only loopback present: no refused request reached the
application, and each refusal carried its specific TLS alert except where a
server close raced it; role and scope came from data, so a scope change took effect on the
same certificate; one credential worked at a second node of the same
deployment; a second deployment's authority was refused; and a node holding the
revocation refused the credential while a partition without it accepted it,
which is CONOPS section 15's stated limitation reproduced, not solved.

The demonstration also showed why the header rule in `services/ingress/` is
load-bearing. With the proxy bypassed, a forged principal header was accepted
as an administrator. With a proxy that forwards rather than sets the header, a
Unit Member's request succeeded as an administrator, which is the
`TBR-TAK-01` bypass reproduced from the other side.

### 4. Time: C and B can enforce `FML-ADR-042` in one place; A cannot

`FML-ADR-042`: certificate validity and expiry checks *"shall not fail open"*
on invalid time. TLS cannot tell that the clock is wrong. Demonstrated: a
certificate not yet valid is refused against the true clock and **verifies OK
against a clock running two days fast**. The time gate therefore has to come
from the node's time-credibility state, not from the TLS library.

Under C that gate is one check at the ingress, demonstrated returning `503`
while time is not credible. Under B the provider can be gated in one place, but
each of six services still validates token expiry against the same clock.
Under A a password login does not consult time at all, so CONOPS section 13's
*time-bounded* credential is bounded only by six products each checking account
expiry against a clock nobody has told them to distrust.

The values, holdover and skew, remain `TBR-TIME-01`'s, which is `OPEN` and
which this trade `depends-on`. The rule needs no values to be stated.

### 5. C's real costs, which an owner would be accepting

- **The browser experience on an EUD is unmeasured.** Whether a phone's browser
  presents a client certificate silently, asks once per service, or asks per
  session decides the selection-prompt cell. Mobile platforms also generally
  keep credentials installed for Wi-Fi apart from those apps and browsers can
  use, so the `FML-ADR-038` credential may need a second install before a
  browser can present it. Both are upstream platform behaviour, stated as
  expectations to test, not observed here. Testing them needs a phone, not a
  MULE.
- **CONOPS section 13 separates network admission from user identity.** One
  certificate doing both is arguably the conflation that section forbids.
  Issuing two credentials from one enrollment keeps them apart at the cost of
  doubling issuance. That is a reading of section 13 for the owner, not for
  this file.
- **A device credential identifies a device's holder, not a person.** An EUD
  handed between people authenticates as whoever it was issued to. CONOPS 16
  requires identity not be bound to one EUD, and reissue satisfies that, but
  nothing in C notices a handover. A and B notice only if they force a fresh
  login.
- **Products have to accept a proxy-asserted principal.** CONOPS 49 leaves
  products to downstream selection; C makes "accepts an authenticated
  principal from the ingress" a selection criterion. OpenTAKServer's browser
  UI is known only to use its own login, so the TAK Administrator would keep
  that one typed event under any option.
- **Backend isolation becomes a security control.** Already a recorded
  requirement: *"The application port shall not be reachable except through
  the proxy."* The demonstration's control case is why.

None of these is unique to C except the first. A and B carry their own forms
of the rest.

### 6. `TBR-ID-01` is cited for more than it asks

`FML-ADR-084` and `mission/README.md` say `TBR-ID-01` *"still owns who may
enroll and how identity becomes an admission credential"*.
`THREAT_MODEL.md` routes *"Client-certificate authentication, lifetime and
revocation on the API path"* here. `services/map/README.md` routes *"how the
map-source definition reaches the EUD"* here. The trade file's question and
closure gate cover none of them, and `docs/ROADMAP-DEV.md` already records that
*"the network-admission pieces exceed its current workflow-analysis scope"*.

So closing `TBR-ID-01` on its own gate would leave three cited owners pointing
at a closed trade that did not answer them. Under C this matters more, because
everything rides on the enrollment credential, so enrollment becomes the
critical path. Whether to widen the trade by change request or open a separate
enrollment trade is the owner's decision. It is recorded here, not made.

## Recommendation, which is not a decision

1. **Do not introduce a common identity provider service.** For the fielded
   catalog there is nothing for it to be common to, and for the planning case
   it adds an S0 component and a capturable signing key to save typed events
   that C saves without either.
2. **Prefer C as the browser-service authentication pattern** for any
   identity-needing service catalogued later, with A as the fallback for a
   product that cannot accept a proxy-asserted principal.
3. **Before selecting C, measure the selection prompt on one Android and one
   iOS EUD.** If a phone asks per session, B's single typed login may be the
   better trade, and this recommendation should be revisited rather than
   defended.
4. **Resolve finding 6 before closing.**

A selection would be an ADR. None is drafted: whether the owner wants one now,
or after the EUD measurement, is the owner's call.

## Closure evidence, item by item

| Closure evidence asks for | State |
| --- | --- |
| Walkthrough, every catalog service, with and without a common IdP, counting events | Above, for the fielded catalog and for the CONOPS 49 planning case. Derived, `UNVERIFIED` |
| Offline login demonstrated with no WAN | For option C against fakes, `SIMULATED`, in the companion artifact. Not for a selected approach, because none is selected |
| Provisioning burden per user per mission | Above, as formulas and one illustration |
| Behaviour when time is not credible | Above, finding 4; the gate demonstrated against fakes |
| A decision recorded, and the role and scope workflow end to end | **Not done.** The owner's. |

`TBR-ID-01` stays `OPEN`.
