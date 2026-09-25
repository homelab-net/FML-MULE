"""Unit tests for the packaged configuration renderer.

The tool's most important behaviour today is what it **refuses** to do. Every
region profile in `regions/` is unresolvable, and the correct result is a
refusal that names the trade which will supply the missing value. The tests
below hold it to that as firmly as they hold it to the success path, because the
failure mode this tool exists to prevent — a plausible default silently becoming
a fielded channel — is a success-shaped failure.

Resolution and validation are exercised against the synthetic fixture region in
`test/fixtures/regions/`, which is deliberately not a real regulatory profile.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from mule import configuration as gc

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGIONS = REPO_ROOT / "test" / "fixtures" / "regions" / "xx-testfixture"
MISSION = REPO_ROOT / "mission" / "examples" / "valid-minimal.json"
MISSION_FULL = REPO_ROOT / "mission" / "examples" / "valid-full.json"
MISSION_UNKNOWN_FIELD = (
    REPO_ROOT / "mission" / "examples" / "invalid-unknown-field.json"
)
#: The shipped ROADMAP v0.0.1 node, resolved under nodes/ by identifier.
NODE_V001 = "mule-v001"
#: A synthetic access-point-only node fixture, loaded by path.
FIXTURE_NODE_AP_ONLY = (
    REPO_ROOT / "test" / "fixtures" / "nodes" / "ap-only" / "node.yml"
)
US_915 = REPO_ROOT / "regions" / "us-915" / "profile.yml"

# --- refusal on TBD ------------------------------------------------------


def test_committed_region_profiles_are_all_unresolved() -> None:
    """A tripwire, not a limitation.

    If this test ever fails, either a trade closed and a profile was filled in
    from evidence, or somebody wrote an invented number into `regions/`. The
    two look identical from here, which is exactly why the failure should be
    read rather than deleted.
    """
    profiles = sorted((REPO_ROOT / "regions").glob("*/profile.yml"))
    assert profiles, "expected at least one region profile"

    for profile in profiles:
        region = gc.load_region(str(profile))
        gaps = gc.unresolved(region)
        assert gaps, f"{profile} resolves; confirm every value traces to evidence"


def test_generation_refuses_and_names_the_trade() -> None:
    with pytest.raises(gc.UnresolvedValueError) as excinfo:
        gc.generate(str(REPO_ROOT / "regions" / "us-915" / "profile.yml"), MISSION)

    message = str(excinfo.value)
    assert "TBD" in message
    assert "TBR-RF-02" in message
    assert "halow.default_channel" in message


def test_unresolved_reports_every_gap_with_its_trade() -> None:
    region = gc.load_region(str(REPO_ROOT / "regions" / "us-915" / "profile.yml"))

    gaps = gc.unresolved(region)

    assert gaps
    assert all(trade.startswith("TBR-") for _, trade in gaps)
    dotted = {path for path, _ in gaps}
    # The AP band/channel/EIRP were set by the TBR-RF-03 AP-params decision
    # (Owner, 2026-09-21), so the AP channel is no longer an unresolved gap.
    assert "wifi.ap_channel" not in dotted
    # The mesh, HaLow and LoRa values remain legitimately TBD (TBR-RF-01/02).
    assert "lora.default_channel" in dotted


def test_check_mode_reports_gaps_and_exits_zero(capsys: pytest.CaptureFixture) -> None:
    """`--check` asks a question; an unresolved answer is not an error."""
    code = gc.main(
        [
            "--region",
            str(REPO_ROOT / "regions" / "us-915" / "profile.yml"),
            "--mission",
            str(MISSION),
            "--check",
        ]
    )

    assert code == 0
    out = capsys.readouterr().out
    assert "still TBD" in out
    assert "TBR-RF-02" in out


def test_check_mode_rejects_an_invalid_mission(
    capsys: pytest.CaptureFixture,
) -> None:
    code = gc.main(
        [
            "--region",
            str(FIXTURE_REGIONS / "profile.yml"),
            "--mission",
            str(MISSION_UNKNOWN_FIELD),
            "--check",
        ]
    )

    assert code == 2
    error = capsys.readouterr().err
    assert "$" in error
    assert "transmit_power_dbm" in error


def test_check_mode_rejects_a_disabled_catalog_service(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Operator preflight applies the same service gates as generation."""
    package = json.loads(MISSION.read_text(encoding="utf-8"))
    package["services"] = ["opentakserver"]
    mission = tmp_path / "mission.json"
    mission.write_text(json.dumps(package), encoding="utf-8")

    code = gc.main(
        [
            "--region",
            str(FIXTURE_REGIONS / "profile.yml"),
            "--mission",
            str(mission),
            "--check",
        ]
    )

    assert code == 2
    assert "disabled catalog service" in capsys.readouterr().err


# --- the success path ----------------------------------------------------


def test_fixture_region_resolves() -> None:
    params = gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION)

    assert params["region"]["id"] == "xx-testfixture"
    assert params["halow"]["channel"] == 905000000
    assert params["lora"]["channel"] == 915000000
    assert params["wifi"]["mesh_channel"] == 149
    assert params["amateur"]["enabled"] is False


def test_generation_rejects_a_mission_package_with_an_unknown_field() -> None:
    """The generator shall not bypass the canonical mission schema."""
    with pytest.raises(gc.ConfigError) as excinfo:
        gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_UNKNOWN_FIELD)

    message = str(excinfo.value)
    assert "schema" in message
    assert "$" in message
    assert "transmit_power_dbm" in message


def test_generation_writes_a_parameter_document(tmp_path: Path) -> None:
    gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION, tmp_path)

    written = json.loads((tmp_path / "parameters.json").read_text(encoding="utf-8"))
    assert written["region"]["id"] == "xx-testfixture"
    assert written["mission"]["example"] is True


def test_the_fixture_region_is_not_loadable_by_identifier() -> None:
    """A fixture must not be reachable the way a deployable profile is."""
    with pytest.raises(gc.ConfigError):
        gc.load_region("xx-testfixture")


# --- validation ----------------------------------------------------------


def test_channel_outside_the_permitted_band_is_rejected() -> None:
    """A generated channel outside the permitted set is a regulatory problem."""
    with pytest.raises(gc.RegionViolationError) as excinfo:
        gc.generate(str(FIXTURE_REGIONS / "profile-out-of-band.yml"), MISSION)

    assert "outside the permitted band" in str(excinfo.value)


def test_amateur_enabled_profile_is_rejected() -> None:
    """Amateur integration is disabled by default in every region."""
    with pytest.raises(gc.RegionViolationError) as excinfo:
        gc.generate(str(FIXTURE_REGIONS / "profile-amateur-enabled.yml"), MISSION)

    assert "amateur" in str(excinfo.value)


@pytest.mark.parametrize(
    ("profile", "fragment"),
    [
        ("profile-bearer-not-permitted.yml", "does not permit this bearer"),
        ("profile-non-numeric-channel.yml", "is not a frequency"),
        ("profile-non-numeric-eirp.yml", "is not a number"),
    ],
    ids=["bearer-forbidden", "channel-not-a-frequency", "eirp-not-a-number"],
)
def test_every_validation_branch_can_actually_fire(profile: str, fragment: str) -> None:
    """Each check in `validate` has a fixture that trips it.

    A regulatory check nobody has ever seen fail is indistinguishable from one
    that cannot fail. The EIRP check was exactly that before this: it compared
    a resolved value against the profile field it had just been copied from,
    so it read as a transmit-power control while being unreachable code.
    """
    with pytest.raises(gc.RegionViolationError) as excinfo:
        gc.generate(str(FIXTURE_REGIONS / profile), MISSION)

    assert fragment in str(excinfo.value)


# --- what the mission package supplies ------------------------------------


def test_the_mission_package_supplies_the_service_list() -> None:
    """Carry the deployment's service list through without supplying one.

    Services are deployment data. The generator never offers a default set.
    """
    full = gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)
    minimal = gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION)

    assert full["mission"]["services"] == ["martin"]
    assert full["network"]["local_domain"] == "example.invalid"

    # The minimal package enables nothing and names no domain. Both are valid.
    assert minimal["mission"]["services"] == []
    assert minimal["network"]["local_domain"] is None


def test_the_mission_package_supplies_the_address_prefix() -> None:
    """FML-ADR-063: the per-deployment IPv4 prefix is carried into config.

    It was previously dropped from the generated network block (GAP-03), so a
    valid prefix never reached configuration. Asserting the resolved value
    equals the package's own fails against that drop (KeyError on the missing
    key). The minimal package omits it, and None is the honest absence.
    """
    full_pkg = json.loads(MISSION_FULL.read_text(encoding="utf-8"))
    expected = full_pkg["network"]["address_prefix"]

    full = gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)
    assert full["network"]["address_prefix"] == expected

    minimal = gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION)
    assert minimal["network"]["address_prefix"] is None


# --- bad input is refused with a message, not a traceback -----------------


@pytest.mark.parametrize(
    ("loader", "argument", "fragment"),
    [
        (lambda p: gc.load_region(str(p)), "missing.yml", "not found"),
        (lambda p: gc.load_mission(p), "missing.json", "not found"),
    ],
    ids=["region-profile-missing", "mission-package-missing"],
)
def test_a_missing_file_is_named_in_the_error(
    tmp_path: Path, loader: object, argument: str, fragment: str
) -> None:
    with pytest.raises(gc.MissingParameterError) as excinfo:
        loader(tmp_path / argument)  # type: ignore[operator]

    assert fragment in str(excinfo.value)
    assert argument in str(excinfo.value)


def test_a_profile_that_is_not_a_mapping_is_refused(tmp_path: Path) -> None:
    """A YAML list or scalar is a file, not a profile.

    Left unchecked this surfaces later as an unrelated attribute error, far
    from the file that caused it.
    """
    bad = tmp_path / "profile.yml"
    bad.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(gc.MissingParameterError) as excinfo:
        gc.load_region(str(bad))

    assert "not a mapping" in str(excinfo.value)


def test_a_package_that_is_not_a_mapping_is_refused(tmp_path: Path) -> None:
    bad = tmp_path / "mission.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(gc.ConfigError) as excinfo:
        gc.load_mission(bad)

    assert "$" in str(excinfo.value)
    assert "not of type 'object'" in str(excinfo.value)


def test_an_absent_key_names_the_path_it_was_looking_for() -> None:
    with pytest.raises(gc.MissingParameterError) as excinfo:
        gc._get({"region": {}}, "region.regulator")

    assert "region.regulator" in str(excinfo.value)


def test_a_profile_that_cannot_name_its_regulator_is_refused(
    tmp_path: Path,
) -> None:
    """Identity is checked before parameters.

    A profile that does not know which authority it derives from cannot be used
    to justify a transmission, whatever else it contains.
    """
    source = (FIXTURE_REGIONS / "profile.yml").read_text(encoding="utf-8")
    anonymous = tmp_path / "profile.yml"
    anonymous.write_text(
        source.replace('regulator: "None. This is a test fixture."', "regulator: TBD"),
        encoding="utf-8",
    )

    with pytest.raises(gc.UnresolvedValueError) as excinfo:
        gc.generate(str(anonymous), MISSION)

    assert "regulator" in str(excinfo.value)


# --- service catalog enforcement (FML-ADR-078) ----------------------------


def test_a_mission_enabling_an_uncatalogued_service_is_refused(tmp_path: Path) -> None:
    """FML-ADR-078: a node runs only services the catalog approves.

    The mission JSON schema requires every service to have a catalog entry but
    cannot check it; resolution does. A package that enables an unknown service
    is refused with a message naming it. Against the old code (no enforcement)
    generation proceeded, so this raised nothing.
    """
    package = json.loads(MISSION.read_text(encoding="utf-8"))
    package["services"] = ["not-a-catalogued-service"]
    bad = tmp_path / "mission.json"
    bad.write_text(json.dumps(package), encoding="utf-8")

    with pytest.raises(gc.ConfigError) as excinfo:
        gc.generate(str(FIXTURE_REGIONS / "profile.yml"), str(bad))

    message = str(excinfo.value)
    assert "no catalog entry" in message
    assert "not-a-catalogued-service" in message


def test_the_catalogued_services_resolve() -> None:
    """A package that enables only catalogued services resolves (FML-ADR-078)."""
    full = gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)
    assert full["mission"]["services"] == ["martin"]


def _use_catalog(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    services: list[dict[str, object]],
) -> None:
    """Point generation at a disposable service catalog and Quadlet directory."""
    path = tmp_path / "services" / "catalog" / "catalog.yml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"services": services}), encoding="utf-8")
    (tmp_path / "services" / "quadlets").mkdir(parents=True)
    monkeypatch.setattr(gc, "CATALOG_PATH", path)


def _service(
    name: str,
    *,
    enabled: bool = True,
    aliases: list[str] | None = None,
    unit: str | None = None,
) -> dict[str, object]:
    """Build the catalog fields configuration generation consumes."""
    return {
        "name": name,
        "enabled": enabled,
        "aliases": aliases or [],
        "unit": unit or f"{name}.container",
        "purpose": "Synthetic unit-test service.",
        "image": "TBD",
        "upstream": {
            "project": "Synthetic test fixture",
            "url": "https://example.invalid/source",
            "license": "test-only",
        },
        "rootless": "TBD",
        "resource_envelope": "TBD",
        "exposed_to": ["node"],
        "durable_state": "TBD",
        "recovery": "TBD",
        "region_dependency": False,
        "adr": "FML-ADR-078",
    }


def test_duplicate_catalog_names_are_refused_before_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Two records with one canonical name cannot become one accidental set entry."""
    services = [_service("opentakserver"), _service("opentakserver")]
    services[1]["purpose"] = "A distinct record reusing the same identity."
    _use_catalog(monkeypatch, tmp_path, services)

    with pytest.raises(gc.ConfigError, match="duplicate service reference"):
        gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)


def test_disabled_catalog_service_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A catalog contract with no deployable unit cannot be enabled by a mission."""
    services = [
        _service("opentakserver", enabled=False, unit="TBD"),
        _service("martin", enabled=False, unit="TBD"),
    ]
    _use_catalog(monkeypatch, tmp_path, services)
    package = json.loads(MISSION_FULL.read_text(encoding="utf-8"))
    package["services"] = ["opentakserver"]

    with pytest.raises(gc.ConfigError, match="disabled catalog service"):
        gc.resolve(gc.load_region(str(FIXTURE_REGIONS / "profile.yml")), package)


def test_catalog_alias_resolves_to_one_canonical_enabled_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An unambiguous alias is normalized before downstream configuration sees it."""
    services = [
        _service("opentakserver", aliases=["tak"]),
        _service("martin"),
    ]
    _use_catalog(monkeypatch, tmp_path, services)
    quadlets = tmp_path / "services" / "quadlets"
    (quadlets / "opentakserver.container").touch()
    (quadlets / "martin.container").touch()
    package = json.loads(MISSION_FULL.read_text(encoding="utf-8"))
    package["services"] = ["tak", "martin"]

    resolved = gc.resolve(gc.load_region(str(FIXTURE_REGIONS / "profile.yml")), package)

    assert resolved["mission"]["services"] == ["opentakserver", "martin"]


def test_enabled_service_without_its_quadlet_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A catalog record is not deployable until its named unit actually exists."""
    services = [_service("opentakserver"), _service("martin")]
    _use_catalog(monkeypatch, tmp_path, services)

    with pytest.raises(gc.ConfigError, match="deployment unit is absent"):
        gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)


def test_enabled_bundle_requires_every_member(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A target with no members is not the capability the catalog named."""
    service = _service("opentakserver", unit="opentakserver.target")
    service["bundle"] = ["postgresql.container", "ots.network"]
    _use_catalog(monkeypatch, tmp_path, [service])
    quadlets = tmp_path / "services" / "quadlets"
    (quadlets / "opentakserver.target").touch()
    (quadlets / "ots.network").touch()

    with pytest.raises(gc.ConfigError, match=r"postgresql\.container"):
        gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)


def test_enabled_bundle_resolves_when_its_members_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The deployment root stays the target once the member files exist."""
    service = _service("opentakserver", unit="opentakserver.target")
    service["bundle"] = ["postgresql.container"]
    _use_catalog(monkeypatch, tmp_path, [service])
    quadlets = tmp_path / "services" / "quadlets"
    (quadlets / "opentakserver.target").touch()
    (quadlets / "postgresql.container").touch()
    package = json.loads(MISSION_FULL.read_text(encoding="utf-8"))
    package["services"] = ["opentakserver"]

    resolved = gc.resolve(gc.load_region(str(FIXTURE_REGIONS / "profile.yml")), package)

    assert resolved["mission"]["services"] == ["opentakserver"]


@pytest.mark.parametrize(
    ("service", "created", "fragment"),
    [
        (
            _service("martin", unit="wrong.container"),
            [],
            "must name deployment unit",
        ),
        (
            _service("martin", unit="martin.container")
            | {"bundle": ["member.container"]},
            [],
            "must name a .target",
        ),
        (
            _service("martin"),
            ["martin.container", "martin.container.disabled"],
            "still has disabled text",
        ),
        (
            _service("martin", enabled=False, unit="martin.container")
            | {"bundle": ["member.container"]},
            [],
            "must name its .target root",
        ),
        (
            _service("martin", enabled=False, unit="martin.target")
            | {"bundle": ["member.container"]},
            ["martin.target"],
            "names loadable unit",
        ),
        (
            _service("martin", enabled=False, unit="martin.container"),
            [],
            "names loadable unit",
        ),
    ],
)
def test_catalog_unit_shape_failures_are_reachable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    service: dict[str, object],
    created: list[str],
    fragment: str,
) -> None:
    """Every catalog deployment-shape refusal shall have a failing fixture."""
    _use_catalog(monkeypatch, tmp_path, [service])
    quadlets = tmp_path / "services" / "quadlets"
    for name in created:
        (quadlets / name).touch()

    with pytest.raises(gc.ConfigError, match=fragment):
        gc.resolve(
            gc.load_region(str(FIXTURE_REGIONS / "profile.yml")), {"services": []}
        )


def test_two_references_to_one_service_are_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One canonical service cannot enter the resolved set twice."""
    _use_catalog(monkeypatch, tmp_path, [_service("martin", aliases=["maps"])])
    (tmp_path / "services/quadlets/martin.container").touch()

    with pytest.raises(gc.ConfigError, match="multiple references"):
        gc.resolve(
            gc.load_region(str(FIXTURE_REGIONS / "profile.yml")),
            {"services": ["martin", "maps"]},
        )


def test_unresolved_treats_an_absent_parameter_as_a_gap() -> None:
    """An absent value shall remain unresolved rather than raising early."""
    region = gc.load_region(str(FIXTURE_REGIONS / "profile.yml"))
    del region["wifi"]["ap_channel"]

    assert ("wifi.ap_channel", "TBR-RF-03") in gc.unresolved(region, ["wifi_ap"])


def test_check_mode_reports_a_fully_resolved_profile(
    capsys: pytest.CaptureFixture,
) -> None:
    """The preflight success branch shall be an observed result."""
    code = gc.main(
        [
            "--region",
            str(FIXTURE_REGIONS / "profile.yml"),
            "--mission",
            str(MISSION),
            "--check",
        ]
    )

    assert code == 0
    assert "all required parameters are resolved" in capsys.readouterr().out


def test_generation_mode_reports_input_errors(capsys: pytest.CaptureFixture) -> None:
    """Non-check invocation shall map ordinary input defects to exit code 2."""
    code = gc.main(
        [
            "--region",
            str(FIXTURE_REGIONS / "profile.yml"),
            "--mission",
            "missing-mission.json",
        ]
    )

    assert code == 2
    assert "ERROR:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "name", ["Martin", "m/artin", "m\N{CYRILLIC SMALL LETTER A}rtin"]
)
def test_malformed_catalog_identifiers_are_refused_before_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    """Case, path and Unicode lookalikes fail the catalog schema at runtime."""
    services = [_service(name)]
    _use_catalog(monkeypatch, tmp_path, services)

    with pytest.raises(gc.ConfigError, match="service catalog schema violation"):
        gc.generate(str(FIXTURE_REGIONS / "profile.yml"), MISSION_FULL)


# --- target-aware resolution (FML-ADR-075) --------------------------------


def test_the_v001_node_declares_only_the_access_point() -> None:
    """The shipped v0.0.1 descriptor fields wifi_ap and nothing else."""
    node = gc.load_node(NODE_V001)

    assert gc.active_targets(node) == ["wifi_ap"]


def test_an_ap_only_node_resolves_against_the_shipped_profile() -> None:
    """Scoping is what unblocks the first-milestone node.

    us-915 leaves the mesh, HaLow and LoRa values TBD, but the Owner set the AP
    band/channel/EIRP (TBR-RF-03 AP-params, 2026-09-21). An AP-only node fields
    only wifi_ap, so it resolves -- it is not refused on the HaLow/LoRa trade
    for bearers it does not field. Without target-awareness this call would
    still raise on TBR-RF-02, so a resolved AP-only node is itself the proof
    that the refusal stays scoped to the node's own bearers. Before the
    decision this same call refused on TBR-RF-03.
    """
    params = gc.generate(str(US_915), MISSION, node_ref=NODE_V001)

    assert "ap_channel" in params["wifi"]
    assert "mesh_channel" not in params["wifi"]
    assert "halow" not in params
    assert "lora" not in params


def test_the_ap_eirp_decision_does_not_resolve_the_mesh_trade() -> None:
    """The AP and mesh EIRP are different decisions (TBR-RF-03 vs TBR-RF-01).

    A single shared `wifi.max_eirp_dbm` field once let the AP-params decision
    (TBR-RF-03) silently resolve the mesh EIRP too -- a plausible default becoming
    a fielded value, the failure this program most fears. With the fields split, a
    mesh-fielding target against us-915 still gaps on its own EIRP, named to its
    own trade. This fails before the split (mesh EIRP resolved by the AP value).
    """
    region = gc.load_region(str(US_915))

    gaps = dict(gc.unresolved(region, ["wifi_mesh"]))

    assert gaps.get("wifi.mesh_max_eirp_dbm") == "TBR-RF-01"
    # And the AP decision did resolve the AP's own EIRP.
    assert "wifi.ap_max_eirp_dbm" not in dict(gc.unresolved(region, ["wifi_ap"]))


def test_an_ap_only_node_emits_only_its_bearer_blocks() -> None:
    """A resolved AP-only node carries its AP parameters and no others.

    A bearer the node does not field contributes no block: emitting a HaLow
    channel for a node with no HaLow radio would put an unfielded value into a
    resolved document.
    """
    params = gc.generate(
        str(FIXTURE_REGIONS / "profile.yml"),
        MISSION,
        node_ref=str(FIXTURE_NODE_AP_ONLY),
    )

    assert "halow" not in params
    assert "lora" not in params
    assert "ap_channel" in params["wifi"]
    assert "mesh_channel" not in params["wifi"]


def test_a_node_with_an_unknown_active_bearer_is_a_hard_error() -> None:
    """An active bearer that is not a known target is surfaced, not skipped."""
    with pytest.raises(gc.ConfigError) as excinfo:
        gc.active_targets({"active_bearers": ["satellite"]})

    message = str(excinfo.value)
    assert "satellite" in message
    assert "no configuration target" in message


def test_a_node_with_no_active_bearers_is_a_hard_error() -> None:
    with pytest.raises(gc.ConfigError) as excinfo:
        gc.active_targets({"node": {"id": "x"}})

    assert "active_bearers" in str(excinfo.value)


def test_check_mode_with_a_node_scopes_to_its_bearers(
    capsys: pytest.CaptureFixture,
) -> None:
    """`--node` narrows even the --check report to the node's own trades.

    mule-v001 fields only wifi_ap, whose parameters the Owner set (TBR-RF-03
    AP-params, 2026-09-21), so its scoped check now resolves -- and never drags
    in the HaLow/LoRa trade (TBR-RF-02) for bearers it does not field. Before
    the decision this scoped check named TBR-RF-03 as still TBD.
    """
    code = gc.main(
        [
            "--region",
            str(US_915),
            "--mission",
            str(MISSION),
            "--node",
            NODE_V001,
            "--check",
        ]
    )

    assert code == 0
    out = capsys.readouterr().out
    assert "all required parameters are resolved" in out
    assert "TBR-RF-02" not in out


def test_a_missing_node_descriptor_is_named(tmp_path: Path) -> None:
    with pytest.raises(gc.MissingParameterError) as excinfo:
        gc.load_node(str(tmp_path / "nope.yml"))

    assert "not found" in str(excinfo.value)


def test_a_node_descriptor_that_is_not_a_mapping_is_refused(tmp_path: Path) -> None:
    bad = tmp_path / "node.yml"
    bad.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(gc.MissingParameterError) as excinfo:
        gc.load_node(str(bad))

    assert "not a mapping" in str(excinfo.value)


# --- exit codes ----------------------------------------------------------


@pytest.mark.parametrize(
    ("profile", "expected_code"),
    [
        ("profile.yml", 0),
        ("profile-out-of-band.yml", 4),
        ("profile-amateur-enabled.yml", 4),
    ],
    ids=["resolves", "out-of-band", "amateur-enabled"],
)
def test_exit_codes_distinguish_the_failure_kinds(
    profile: str, expected_code: int
) -> None:
    """Distinct codes so a caller can tell a refusal from a rejection.

    0 resolved, 2 error, 3 refused because a value is TBD, 4 rejected because a
    resolved value is not permitted. A pipeline that treats them alike cannot
    report the difference between "not decided yet" and "not allowed".
    """
    code = gc.main(
        [
            "--region",
            str(FIXTURE_REGIONS / profile),
            "--mission",
            str(MISSION),
        ]
    )

    assert code == expected_code


def test_refusal_exit_code_is_distinct_from_rejection() -> None:
    code = gc.main(
        [
            "--region",
            str(REPO_ROOT / "regions" / "us-915" / "profile.yml"),
            "--mission",
            str(MISSION),
        ]
    )

    assert code == 3
