# Safety

Read this before you assemble anything.

**This is a hobbyist and volunteer engineering project. It is not a certified
product.** Nothing here has been through product safety testing, environmental
qualification, or independent review. There is no manufacturer standing behind
a device you build from this repository, and there is no warranty of any kind.
A builder who follows this documentation assumes the risk of doing so, for
themselves and for anyone near the equipment they build.

The program is pre-PDR. No enclosure, battery, cell chemistry, charger, or
thermal design has been selected. The guidance below is generic good practice
for the class of device MULE will be. It is not a safety case for a specific
build, because no specific build exists.

## Lithium cells and packs

Most of the realistic harm from a device like this comes from its battery. A
lithium cell failure is fast, very hot, self-sustaining, and produces toxic
smoke. It is not a fire you put out with a domestic extinguisher; it is a fire
you get away from.

### Sourcing

- Buy cells from a **verified source**: the manufacturer, or a distributor who
  can identify the manufacturer and the cell model. Counterfeit and relabelled
  cells are common, and a relabelled cell's capacity, current rating, and
  internal protection are all unknown.
- A cell with a capacity claim well above the best cells that manufacturer
  actually produces is counterfeit. Treat the claim itself as the evidence.
- Record what you bought and from whom. If the cell later misbehaves, that
  record is how anyone else learns from it.

### Protection

- **Protection circuitry is required.** Every pack shall include protection
  against overcharge, over-discharge, overcurrent, and short circuit, whether
  through a protection circuit module, a battery management system, or both, as
  appropriate to the pack topology.
- **No loose cells in unqualified holders.** Spring-contact holders for
  high-drain lithium cells are a poor mechanical and electrical connection.
  They work loose, they arc, and they allow a cell to be inserted reversed.
  Cells shall be retained in a fixture designed for the chemistry and current.
- Multi-cell packs shall be balanced. An unbalanced series pack drives
  individual cells outside their safe window while the pack voltage looks
  correct.
- Never solder directly to a cylindrical cell body unless you have the training
  and equipment to do so; spot-weld tabs instead. Heat damages the internal
  separator in ways you cannot see.

### Charging

- **Charging shall be supervised** at this stage of the program. Do not leave a
  prototype charging unattended, and do not charge overnight.
- Charge on a non-combustible surface, away from anything flammable, and away
  from exits.
- Use a charger matched to the chemistry and cell count. A charger set for the
  wrong chemistry is a fire.
- Do not charge a cell below freezing. Lithium plating from cold charging
  causes an internal short that may appear days later.

### Damage and quarantine

- Any pack that has been dropped hard, punctured, crushed, submerged,
  overheated, swollen, or that shows an unexplained voltage drop shall be
  **quarantined**: removed from service, labelled with the date and reason,
  and stored in a non-combustible container away from anything that will burn,
  outdoors or in an unoccupied structure where practical.
- A damaged pack may fail hours or days after the event. Quarantine is not a
  waiting period after which the pack is fine; it is a holding step before
  disposal.
- Do not return a quarantined pack to service. The cost of a replacement pack
  is not comparable to the cost of the failure mode.

### Storage

- Store at partial charge, not full and not empty. Around half charge is the
  usual guidance for long-term storage; follow the cell manufacturer's figure.
- Store cool and dry. Heat ages cells and raises the risk of a runaway event.
- Store packs so terminals cannot short against each other, against tools, or
  against the container.

### Transport

- Lithium batteries are **regulated dangerous goods** for air transport, and
  in many jurisdictions for commercial ground shipment. Rules cover state of
  charge, packaging, labelling, and quantity, and they differ between cells
  installed in equipment, cells packed with equipment, and loose cells.
- Damaged or defective cells are subject to stricter rules and are commonly
  prohibited from air transport entirely.
- Check the current rules for your carrier and your route before shipping. A
  volunteer deployment that ships equipment is subject to the same rules as
  anyone else.

### Disposal

- Do not put lithium cells in household waste or general recycling. They start
  fires in collection vehicles and at sorting facilities.
- Use a battery-recycling route that accepts lithium chemistry. Tape the
  terminals before handing the cell over.

## Thermal

A sealed enclosure is a thermal problem, and MULE is expected to be a sealed
enclosure carrying a compute element and several transmitting radios under
sustained load, potentially in direct sun.

- **Sealing and cooling are in tension.** Ingress protection removes the
  airflow the parts inside were characterised with. A module rated for a given
  ambient in free air is not rated for that ambient inside a closed box.
- Radios dissipate power whether or not the link is carrying traffic. Power
  amplifiers are frequently the hottest components in a device like this.
- Silicon that throttles is the good outcome. Silicon that does not throttle,
  or a cell that sits next to something hot, is the bad one. **Cells shall be
  thermally separated from heat-producing components**; elevated temperature is
  a direct contributor to cell ageing and to runaway risk.
- External surfaces can reach temperatures that burn skin. This has not been
  characterised for any MULE configuration.
- Thermal architecture is an **open trade**: `TBR-THERM-01`. No thermal claim,
  ambient rating, duty-cycle limit, or surface-temperature figure appears
  anywhere in this repository, because none has been measured.

## Electrical

- Assume the pack is always live. There is no off switch on a battery.
- Fuse the pack side of the power distribution. A short in the wiring harness
  is otherwise limited only by what the cells can deliver, which is a great
  deal.
- Strain-relieve every conductor that leaves a board. Vibration and handling
  break wires at the joint, and a broken conductor inside a sealed enclosure
  can short.
- Verify polarity before first power-on, with a meter, every time.

## Field and operational safety

- This equipment does not replace a working voice plan or a manual fallback
  procedure. See `docs/NON-GOALS.md`. A device that fails silently and was the
  only plan is a safety issue, not a technical one.
- Antennas and masts near overhead power lines are a lethal hazard. Assume any
  overhead line is live and keep separation greater than the total height of
  anything you are raising.
- Do not deploy into an active incident unless your organisation has asked you
  to and the incident's command structure knows you are there.
- Nothing in this repository has been evaluated for use in an environment where
  a failure would endanger someone. Do not use it that way.

## Reporting a safety problem

If you find a safety defect in this documentation or in a design it describes,
open an issue using the hardware finding template, or contact a maintainer
listed in `MAINTAINERS.md`. Safety findings are not embargoed and do not follow
the vulnerability disclosure process in `SECURITY.md`; they are published as
soon as they are understood.
