"""Tests for the SQLite persistence layer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rainrs_server.models import (
    STATUS_NO_FEATURES,
    STATUS_PROCESSED,
    MasterKey,
    RippleAttributes,
    RippleDetection,
    SlaveKey,
)
from rainrs_server.storage.database import (
    count_images,
    find_master_key_for_image,
    list_image_ids,
    list_slave_keys,
    load_image,
    load_master_key,
    load_ripples,
    open_database,
    store_image,
    store_master_key,
    store_slave_key,
)


def _attributes(source: str = "/captures/a.jpg") -> RippleAttributes:
    return RippleAttributes(
        source_path=source,
        image_width=200,
        image_height=113,
        detected_at="2026-10-22T10:00:00+00:00",
        ripples=(
            RippleDetection(
                index=0,
                center_x=100.0,
                center_y=56.5,
                radius=8.0,
                width=16.0,
                height=16.0,
                confidence=0.9,
            ),
            RippleDetection(
                index=1,
                center_x=20.0,
                center_y=10.0,
                radius=4.0,
                width=8.0,
                height=8.0,
                confidence=0.4,
            ),
        ),
    )


def test_schema_is_created(tmp_path: Path) -> None:
    database = tmp_path / "rainrs.db"
    with open_database(database) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {"images", "ripples", "master_keys", "slave_keys"} <= tables


def test_store_and_load_image(tmp_path: Path) -> None:
    database = tmp_path / "rainrs.db"
    with open_database(database) as connection:
        image_id = store_image(connection, _attributes())
        assert image_id > 0

        loaded = load_image(connection, image_id)
        assert loaded is not None
        assert loaded.count == 2
        assert loaded.image_id == image_id
        assert loaded.mean_radius == pytest.approx(6.0)

        ripples = load_ripples(connection, image_id)
        assert [r.index for r in ripples] == [0, 1]
        assert ripples[0].center_x == pytest.approx(100.0)

        assert count_images(connection) == 1
        assert list_image_ids(connection) == [image_id]


def test_store_image_rejects_unknown_status(tmp_path: Path) -> None:
    with open_database(tmp_path / "rainrs.db") as connection:
        with pytest.raises(ValueError):
            store_image(connection, _attributes(), status="bogus")


def test_store_image_without_features(tmp_path: Path) -> None:
    empty = RippleAttributes(
        source_path="/captures/b.jpg",
        image_width=10,
        image_height=10,
        detected_at="2026-10-22T10:00:00+00:00",
    )
    with open_database(tmp_path / "rainrs.db") as connection:
        image_id = store_image(connection, empty, status=STATUS_NO_FEATURES)
        assert load_ripples(connection, image_id) == []


def test_master_and_slave_key_relationship(tmp_path: Path) -> None:
    database = tmp_path / "rainrs.db"
    with open_database(database) as connection:
        image_id = store_image(connection, _attributes())

        master = MasterKey(
            image_id=image_id,
            key="a1b2c3d4e5f60718",
            bits=64,
            algorithm="rk4",
            parameters={"mean_radius": 6.0},
            derived_at="2026-10-22T10:00:00+00:00",
        )
        master_id = store_master_key(connection, master)
        assert master_id > 0

        for index in (0, 1):
            store_slave_key(
                connection,
                SlaveKey(
                    master_key_id=master_id,
                    image_id=image_id,
                    ripple_index=index,
                    key=f"{index:016x}",
                    bits=64,
                    algorithm="rk4/hmac",
                    derived_at="2026-10-22T10:00:00+00:00",
                ),
            )

        slaves = list_slave_keys(connection, master_id)
        assert len(slaves) == 2
        assert all(slave.master_key_id == master_id for slave in slaves)
        assert all(slave.image_id == image_id for slave in slaves)

        found = find_master_key_for_image(connection, image_id)
        assert found is not None
        assert found.key == master.key
        assert load_master_key(connection, master_id) is not None


def test_only_one_master_key_per_image(tmp_path: Path) -> None:
    with open_database(tmp_path / "rainrs.db") as connection:
        image_id = store_image(connection, _attributes())
        master = MasterKey(
            image_id=image_id,
            key="0" * 16,
            bits=64,
            algorithm="rk4",
            parameters={},
            derived_at="2026-10-22T10:00:00+00:00",
        )
        store_master_key(connection, master)
        with pytest.raises(sqlite3.IntegrityError):
            store_master_key(connection, master)


def test_deleting_master_key_cascades_to_slave_keys(tmp_path: Path) -> None:
    from rainrs_server.storage.database import delete_master_key_for_image

    with open_database(tmp_path / "rainrs.db") as connection:
        image_id = store_image(connection, _attributes())
        master_id = store_master_key(
            connection,
            MasterKey(
                image_id=image_id,
                key="1" * 16,
                bits=64,
                algorithm="rk4",
                parameters={},
                derived_at="2026-10-22T10:00:00+00:00",
            ),
        )
        store_slave_key(
            connection,
            SlaveKey(
                master_key_id=master_id,
                image_id=image_id,
                ripple_index=0,
                key="2" * 16,
                bits=64,
                algorithm="rk4/hmac",
                derived_at="2026-10-22T10:00:00+00:00",
            ),
        )
        assert delete_master_key_for_image(connection, image_id) == 1
        assert list_slave_keys(connection, master_id) == []


def test_processed_status_is_the_default(tmp_path: Path) -> None:
    with open_database(tmp_path / "rainrs.db") as connection:
        image_id = store_image(connection, _attributes())
        row = connection.execute(
            "SELECT status FROM images WHERE id = ?", (image_id,)
        ).fetchone()
        assert row["status"] == STATUS_PROCESSED
