# Power

Battery, charging, distribution, and protection for this block.

**Status: `TBD`. No cell, pack, charger, or power budget selected.** See
`TBR-PWR-01`.

**Read `SAFETY.md` before doing anything in this directory.** Most of the
realistic harm from a device like this comes from its battery.

## What belongs here

- **Cell and pack**: chemistry, cell model, configuration, capacity, and the
  archived cell datasheet.
- **Protection**: the protection circuit module or battery management system,
  and what it protects against.
- **Charging**: the charger, the profile, and whether charging happens in situ
  or on a bench.
- **Distribution**: the rails, the regulators, and what each feeds.
- **Fusing**: on the pack side. A short in the harness is otherwise limited
  only by what the cells can deliver.
- **Measured power budget**, per load and in total, once measured.
- **Measured endurance**, with the duty cycle it assumed.

## Rules

- **Protection circuitry is required** on every pack.
- **No loose cells in unqualified holders.** Spring-contact holders for
  high-drain lithium cells work loose, arc, and allow reversed insertion.
- **Cells are thermally separated from heat-producing components.** Elevated
  temperature contributes directly to cell ageing and to runaway risk. See
  `TBR-THERM-01`.
- **Verified cell sources only.** Counterfeit and relabelled cells are common,
  and their real capacity, current rating and internal protection are unknown.
- **Archive the cell datasheet**, including capacity at the discharge rate
  actually used rather than the headline figure.

## No numbers here

No endurance figure, power budget, cell count, capacity, or mass appears
anywhere in this repository, because none has been set or measured. Any number
encountered elsewhere claiming to be a MULE endurance figure did not come from
this program.

`TBR-PWR-01` closes on a measured discharge run of an assembled pack under a
representative load, not on a calculation. Cells do not deliver their datasheet
capacity under real loads at real temperatures.

## Transport and disposal

Lithium batteries are regulated dangerous goods for air transport and, in many
jurisdictions, for commercial ground shipment. Damaged cells are commonly
prohibited from air transport entirely. Disposal goes through a
battery-recycling route that accepts lithium chemistry, with the terminals
taped. See `SAFETY.md`.
