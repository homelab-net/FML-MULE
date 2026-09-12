"""Unit tests for tools/gen-config.py.

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

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

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


def _load() -> ModuleType:
    """Load the hyphenated executable script as a module."""
    path = REPO_ROOT / "tools" / "gen-config.py"
    spec = importlib.util.spec_from_file_location("gen_config_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gc = _load()


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
    assert "wifi.ap_channel" in dotted
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

    assert full["mission"]["services"] == ["opentakserver", "martin"]
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
    assert full["mission"]["services"] == ["opentakserver", "martin"]


# --- target-aware resolution (FML-ADR-075) --------------------------------


def test_the_v001_node_declares_only_the_access_point() -> None:
    """The shipped v0.0.1 descriptor fields wifi_ap and nothing else."""
    node = gc.load_node(NODE_V001)

    assert gc.active_targets(node) == ["wifi_ap"]


def test_an_ap_only_node_refuses_only_on_the_trade_for_its_own_bearer() -> None:
    """Scoping is what unblocks the first-milestone node.

    us-915 has every value TBD. An AP-only node is still refused -- its own AP
    channel is TBD (TBR-RF-03) -- but only on that, not on the HaLow/LoRa trade
    for bearers it does not field. Without target-awareness the refusal named
    every bearer's trade, which is what the absence assertions below catch.
    """
    with pytest.raises(gc.UnresolvedValueError) as excinfo:
        gc.generate(str(US_915), MISSION, node_ref=NODE_V001)

    message = str(excinfo.value)
    assert "wifi.ap_channel" in message
    assert "TBR-RF-03" in message
    assert "halow" not in message
    assert "lora" not in message
    assert "TBR-RF-02" not in message


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
    """`--node` narrows even the --check report to the node's own trades."""
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
    assert "TBR-RF-03" in out
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
