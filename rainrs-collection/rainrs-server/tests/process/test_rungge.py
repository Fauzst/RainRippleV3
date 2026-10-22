"""Tests for the Runge-Kutta key derivation stage."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from rainrs_server.model.detection import RippleAttributes, RippleDetection
from rainrs_server.output.database import (
    find_master_key_for_image,
    list_slave_keys,
    open_database,
    store_image,
)
from rainrs_server.process.rungge import (
    ALGORITHM,
    BINDING_HMAC,
    BINDING_XOR,
    KeyDeriver,
    RippleWaveSystem,
    derive_master_key,
    derive_slave_keys,
    parameters_for_master,
    parameters_for_ripple,
    rk4_integrate,
    rk4_step,
)


def _attributes(ripples: tuple[RippleDetection, ...]) -> RippleAttributes:
    return RippleAttributes(
        source_path="/captures/a.jpg",
        image_width=200,
        image_height=113,
        detected_at="2026-10-22T10:00:00+00:00",
        ripples=ripples,
    )


def _three_ripples() -> tuple[RippleDetection, ...]:
    return (
        RippleDetection(
            index=0,
            center_x=40.0,
            center_y=30.0,
            radius=6.0,
            width=12.0,
            height=12.0,
            confidence=0.81,
        ),
        RippleDetection(
            index=1,
            center_x=120.0,
            center_y=60.0,
            radius=9.0,
            width=18.0,
            height=18.0,
            confidence=0.93,
        ),
        RippleDetection(
            index=2,
            center_x=170.0,
            center_y=90.0,
            radius=4.5,
            width=9.0,
            height=9.0,
            confidence=0.55,
        ),
    )


# ---------------------------------------------------------------------------
# Runge-Kutta core
# ---------------------------------------------------------------------------
def test_rk4_step_solves_the_exponential() -> None:
    derivative = lambda t, y: (y[0],)  # noqa: E731 - compact test double
    state = rk4_step(derivative, 0.0, (1.0,), 0.1)
    assert state[0] == pytest.approx(math.exp(0.1), rel=1e-6)


def test_rk4_integrate_converges_to_the_analytic_solution() -> None:
    derivative = lambda t, y: (y[0],)  # noqa: E731 - compact test double
    samples = rk4_integrate(derivative, (1.0,), dt=0.001, steps=1000, sample_every=1)
    assert samples[-1][0] == pytest.approx(math.e, rel=1e-9)
    assert len(samples) == 1001


def test_rk4_integrate_validates_its_arguments() -> None:
    derivative = lambda t, y: (y[0],)  # noqa: E731 - compact test double
    with pytest.raises(ValueError):
        rk4_integrate(derivative, (1.0,), dt=0.0)
    with pytest.raises(ValueError):
        rk4_integrate(derivative, (1.0,), steps=0)
    with pytest.raises(ValueError):
        rk4_integrate(derivative, (1.0,), sample_every=0)


def test_wave_system_is_deterministic() -> None:
    parameters = parameters_for_ripple(_three_ripples()[0], 200, 113)
    system = RippleWaveSystem(parameters)
    first = rk4_integrate(system, (0.2, 0.3, 0.3, 0.2), steps=200, sample_every=50)
    second = rk4_integrate(system, (0.2, 0.3, 0.3, 0.2), steps=200, sample_every=50)
    assert first == second


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------
def test_master_key_uses_the_averaged_attributes(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    attributes = _attributes(sample_ripples)
    master = derive_master_key(attributes, bits=64)

    assert master.algorithm == ALGORITHM
    assert master.bits == 64
    assert len(master.key) == 16
    int(master.key, 16)  # valid hex
    assert master.parameters["ripple_count"] == 3.0
    assert master.parameters["mean_radius"] == pytest.approx(6.5)


def test_master_key_requires_at_least_one_ripple() -> None:
    with pytest.raises(ValueError):
        derive_master_key(_attributes(()))


def test_master_key_rejects_unsupported_sizes(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    with pytest.raises(ValueError):
        derive_master_key(_attributes(sample_ripples), bits=48)


def test_key_derivation_is_deterministic(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    attributes = _attributes(sample_ripples)
    assert derive_master_key(attributes).key == derive_master_key(attributes).key


def test_different_attributes_give_different_master_keys(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    first = derive_master_key(_attributes(sample_ripples))
    shifted = tuple(
        RippleDetection(
            index=r.index,
            center_x=r.center_x + 1.0,
            center_y=r.center_y,
            radius=r.radius,
            width=r.width,
            height=r.height,
            confidence=r.confidence,
        )
        for r in sample_ripples
    )
    second = derive_master_key(_attributes(shifted))
    assert first.key != second.key


def test_one_slave_key_per_ripple(sample_ripples: tuple[RippleDetection, ...]) -> None:
    attributes = _attributes(sample_ripples)
    master = derive_master_key(attributes)
    slaves = derive_slave_keys(attributes, master)

    assert len(slaves) == attributes.count
    assert [slave.ripple_index for slave in slaves] == [0, 1, 2]
    assert len({slave.key for slave in slaves}) == 3
    assert all(slave.bits == master.bits for slave in slaves)


def test_slave_keys_are_bound_to_the_master_key(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    attributes = _attributes(sample_ripples)
    master = derive_master_key(attributes)
    slaves = derive_slave_keys(attributes, master, binding=BINDING_HMAC)

    other_master = derive_master_key(
        _attributes(
            tuple(
                RippleDetection(
                    index=r.index,
                    center_x=r.center_x,
                    center_y=r.center_y,
                    radius=r.radius + 0.25,
                    width=r.width,
                    height=r.height,
                    confidence=r.confidence,
                )
                for r in sample_ripples
            )
        )
    )
    other_slaves = derive_slave_keys(attributes, other_master, binding=BINDING_HMAC)

    assert [s.key for s in slaves] != [s.key for s in other_slaves]


def test_xor_binding_is_available(sample_ripples: tuple[RippleDetection, ...]) -> None:
    attributes = _attributes(sample_ripples)
    master = derive_master_key(attributes)
    hmac_slaves = derive_slave_keys(attributes, master, binding=BINDING_HMAC)
    xor_slaves = derive_slave_keys(attributes, master, binding=BINDING_XOR)

    assert [s.key for s in hmac_slaves] != [s.key for s in xor_slaves]
    assert all(s.algorithm.endswith(BINDING_XOR) for s in xor_slaves)


def test_unknown_binding_is_rejected(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    attributes = _attributes(sample_ripples)
    master = derive_master_key(attributes)
    with pytest.raises(ValueError):
        derive_slave_keys(attributes, master, binding="rot13")


def test_master_parameters_follow_the_attributes(
    sample_ripples: tuple[RippleDetection, ...],
) -> None:
    parameters = parameters_for_master(_attributes(sample_ripples))
    assert parameters.forcing > 0
    assert parameters.mu > 0
    assert 0.0 <= parameters.phase <= 2.0 * math.pi


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def test_deriver_stores_master_and_slave_keys(
    tmp_path: Path, sample_ripples: tuple[RippleDetection, ...]
) -> None:
    database = tmp_path / "rainrs.db"
    attributes = _attributes(sample_ripples)
    with open_database(database) as connection:
        image_id = store_image(connection, attributes)

    deriver = KeyDeriver(database_path=database, bits=64)
    master, slaves = deriver.derive_for_image(image_id)

    assert master.image_id == image_id
    assert len(slaves) == 3

    with open_database(database) as connection:
        stored = find_master_key_for_image(connection, image_id)
        assert stored is not None
        assert stored.key == master.key

        master_row = connection.execute(
            "SELECT id FROM master_keys WHERE image_id = ?", (image_id,)
        ).fetchone()
        master_id = int(master_row["id"])

        stored_slaves = list_slave_keys(connection, master_id)
        assert len(stored_slaves) == 3
        assert all(slave.master_key_id == master_id for slave in stored_slaves)
        assert all(slave.image_id == image_id for slave in stored_slaves)


def test_deriver_skips_captures_without_ripples(tmp_path: Path) -> None:
    database = tmp_path / "rainrs.db"
    empty = RippleAttributes(
        source_path="/captures/empty.jpg",
        image_width=10,
        image_height=10,
        detected_at="2026-10-22T10:00:00+00:00",
    )
    with open_database(database) as connection:
        store_image(connection, empty)

    deriver = KeyDeriver(database_path=database)
    assert deriver.derive_for_all() == []


def test_deriver_does_not_duplicate_keys(
    tmp_path: Path, sample_ripples: tuple[RippleDetection, ...]
) -> None:
    database = tmp_path / "rainrs.db"
    with open_database(database) as connection:
        image_id = store_image(connection, _attributes(sample_ripples))

    deriver = KeyDeriver(database_path=database)
    first_master, first_slaves = deriver.derive_for_image(image_id)
    second_master, second_slaves = deriver.derive_for_image(image_id)

    assert second_master.key == first_master.key
    assert second_slaves == []

    with open_database(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS total FROM master_keys"
        ).fetchone()
        assert int(count["total"]) == 1


def test_deriver_overwrite_replaces_the_keys(
    tmp_path: Path, sample_ripples: tuple[RippleDetection, ...]
) -> None:
    database = tmp_path / "rainrs.db"
    with open_database(database) as connection:
        image_id = store_image(connection, _attributes(sample_ripples))

    KeyDeriver(database_path=database).derive_for_image(image_id)
    deriver = KeyDeriver(database_path=database, overwrite=True)
    deriver.derive_for_image(image_id)

    with open_database(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS total FROM master_keys"
        ).fetchone()
        assert int(count["total"]) == 1
        slaves = connection.execute(
            "SELECT COUNT(*) AS total FROM slave_keys"
        ).fetchone()
        assert int(slaves["total"]) == 3


def test_deriver_reports_unknown_images(tmp_path: Path) -> None:
    deriver = KeyDeriver(database_path=tmp_path / "rainrs.db")
    with pytest.raises(LookupError):
        deriver.derive_for_image(42)
