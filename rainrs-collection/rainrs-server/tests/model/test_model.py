"""Tests for the dataclasses of the data model."""

from __future__ import annotations

from rainrs_server.model.base import utc_now_iso
from rainrs_server.model.detection import RippleAttributes, RippleDetection
from rainrs_server.model.keys import MasterKey, SlaveKey
from rainrs_server.model.outcome import STATUS_ERROR, ImageOutcome
from rainrs_server.model.state import RippleWaveParameters


def _ripple() -> RippleDetection:
    return RippleDetection(
        index=0,
        center_x=100.0,
        center_y=56.5,
        radius=8.0,
        width=16.0,
        height=16.0,
        confidence=0.87,
    )


def _attributes() -> RippleAttributes:
    return RippleAttributes(
        source_path="/captures/a.jpg",
        image_width=200,
        image_height=113,
        detected_at="2026-10-22T10:00:00+00:00",
        ripples=(_ripple(),),
    )


def test_detection_round_trip() -> None:
    """A detection survives the JSON representation."""
    ripple = _ripple()

    assert RippleDetection.from_dict(ripple.to_dict()) == ripple


def test_attributes_round_trip() -> None:
    """The attribute document survives the JSON representation."""
    attributes = _attributes()

    restored = RippleAttributes.from_dict(attributes.to_dict())

    assert restored == attributes
    assert restored.count == 1
    assert restored.mean_center_x == 100.0


def test_attributes_without_ripples() -> None:
    """Empty attributes report zero averages instead of raising."""
    attributes = RippleAttributes(
        source_path="/captures/a.jpg",
        image_width=0,
        image_height=0,
        detected_at="2026-10-22T10:00:00+00:00",
    )

    assert attributes.count == 0
    assert attributes.mean_center_x == 0.0
    assert attributes.mean_center_y == 0.0
    assert attributes.mean_radius == 0.0


def test_with_storage_fills_in_the_identifiers() -> None:
    """The storage identifiers are filled in through a copy."""
    attributes = _attributes()

    located = attributes.with_storage(image_id=7, stored_path="/processed/a.jpg")

    assert located.image_id == 7
    assert located.stored_path == "/processed/a.jpg"
    assert attributes.image_id is None
    assert attributes.stored_path is None


def test_with_storage_keeps_the_current_values() -> None:
    """An omitted identifier keeps the current one."""
    located = _attributes().with_storage(image_id=7).with_storage(stored_path="/p.jpg")

    assert located.image_id == 7
    assert located.stored_path == "/p.jpg"


def test_master_key_with_image_id() -> None:
    """The image identifier of a master key is set through a copy."""
    master = MasterKey(
        image_id=0,
        key="aabb",
        bits=32,
        algorithm="rk4-vandepol-sha256",
        parameters={"mean_radius": 8.0},
        derived_at="2026-10-22T10:00:00+00:00",
    )

    bound = master.with_image_id(3)

    assert bound.image_id == 3
    assert bound.key == master.key
    assert master.image_id == 0


def test_slave_key_with_master_key_id() -> None:
    """The master key identifier of a slave key is set through a copy."""
    slave = SlaveKey(
        master_key_id=0,
        image_id=1,
        ripple_index=0,
        key="ccdd",
        bits=32,
        algorithm="rk4-vandepol-sha256/hmac",
        derived_at="2026-10-22T10:00:00+00:00",
    )

    bound = slave.with_master_key_id(9)

    assert bound.master_key_id == 9
    assert bound.ripple_index == 0
    assert slave.master_key_id == 0


def test_image_outcome_succeeded() -> None:
    """Only the processed status counts as a success."""
    assert ImageOutcome(source="a.jpg", status="processed").succeeded
    assert not ImageOutcome(source="a.jpg", status=STATUS_ERROR).succeeded


def test_wave_parameters_to_dict() -> None:
    """The oscillator parameters have a plain dictionary form."""
    parameters = RippleWaveParameters(mu=1.0, coupling=2.0, forcing=3.0, phase=0.5)

    assert parameters.to_dict() == {
        "mu": 1.0,
        "coupling": 2.0,
        "forcing": 3.0,
        "phase": 0.5,
    }


def test_utc_now_iso_is_utc() -> None:
    """The shared timestamp format is an ISO 8601 UTC string."""
    stamp = utc_now_iso()

    assert stamp.endswith("+00:00")
    assert "T" in stamp
