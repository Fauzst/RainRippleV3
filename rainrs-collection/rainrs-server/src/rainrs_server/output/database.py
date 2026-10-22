"""SQLite persistence for ripple features and derived research keys.

The database is the *output* layer of the pipeline: it stores the
extracted attributes and the derived research artifacts. It holds four
tables:

``images``
    One row per processed capture: the source path, the image geometry,
    the number of detected ripples, the processing status and the full
    JSON attribute document.
``ripples``
    One row per detected ripple, referencing ``images(id)``.
``master_keys``
    Exactly one master key per image (enforced by a ``UNIQUE``
    constraint on ``image_id``).
``slave_keys``
    One row per detected ripple, referencing the master key it belongs
    to through ``master_key_id``.

Usage::

    from rainrs_server.output.database import open_database

    with open_database(paths.database) as connection:
        image_id = store_image(connection, attributes)

The database file lives in ``storage/rainrs.db`` and is excluded from
version control: it contains derived features and key material.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..model.detection import RippleAttributes, RippleDetection
from ..model.keys import MasterKey, SlaveKey
from ..model.outcome import STATUS_ERROR, STATUS_NO_FEATURES, STATUS_PROCESSED

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path   TEXT    NOT NULL,
    stored_path   TEXT,
    image_width   INTEGER NOT NULL,
    image_height  INTEGER NOT NULL,
    ripple_count  INTEGER NOT NULL,
    status        TEXT    NOT NULL,
    error         TEXT,
    features_json TEXT    NOT NULL,
    processed_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS ripples (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id     INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    ripple_index INTEGER NOT NULL,
    center_x     REAL    NOT NULL,
    center_y     REAL    NOT NULL,
    radius       REAL    NOT NULL,
    width        REAL    NOT NULL,
    height       REAL    NOT NULL,
    confidence   REAL    NOT NULL,
    UNIQUE (image_id, ripple_index)
);

CREATE TABLE IF NOT EXISTS master_keys (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id       INTEGER NOT NULL UNIQUE REFERENCES images(id) ON DELETE CASCADE,
    master_key     TEXT    NOT NULL,
    bits           INTEGER NOT NULL,
    algorithm      TEXT    NOT NULL,
    parameters_json TEXT   NOT NULL,
    derived_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS slave_keys (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    master_key_id  INTEGER NOT NULL REFERENCES master_keys(id) ON DELETE CASCADE,
    image_id       INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    ripple_index   INTEGER NOT NULL,
    slave_key      TEXT    NOT NULL,
    bits           INTEGER NOT NULL,
    algorithm      TEXT    NOT NULL,
    derived_at     TEXT    NOT NULL,
    UNIQUE (master_key_id, ripple_index)
);

CREATE INDEX IF NOT EXISTS idx_ripples_image ON ripples(image_id);
CREATE INDEX IF NOT EXISTS idx_slave_keys_master ON slave_keys(master_key_id);
"""


@contextmanager
def open_database(path: Path) -> Iterator[sqlite3.Connection]:
    """Open (and initialise) the SQLite database at ``path``.

    The connection is closed when the context manager exits. Foreign key
    enforcement is switched on so that cascades behave as documented.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        initialize_schema(connection)
        yield connection
    finally:
        connection.close()


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the tables and indexes if they do not exist yet."""
    connection.executescript(_SCHEMA)
    connection.commit()


def store_image(
    connection: sqlite3.Connection,
    attributes: RippleAttributes,
    *,
    status: str = STATUS_PROCESSED,
    error: str | None = None,
) -> int:
    """Insert an image row (and its ripple rows) and return the new id.

    Args:
        connection: An open database connection.
        attributes: The extracted attributes of the capture.
        status: One of ``processed``, ``no_features`` or ``error``.
        error: Error message, stored when ``status`` is ``error``.
    """
    if status not in {STATUS_PROCESSED, STATUS_NO_FEATURES, STATUS_ERROR}:
        raise ValueError(f"unsupported image status: {status}")

    payload = attributes.to_dict()
    payload["image_id"] = None
    cursor = connection.execute(
        """
        INSERT INTO images (
            source_path, stored_path, image_width, image_height,
            ripple_count, status, error, features_json, processed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attributes.source_path,
            attributes.stored_path,
            attributes.image_width,
            attributes.image_height,
            attributes.count,
            status,
            error,
            json.dumps(payload, sort_keys=True),
            attributes.detected_at,
        ),
    )
    image_id = int(cursor.lastrowid or 0)

    # The stored document references the row it belongs to.
    payload["image_id"] = image_id
    connection.execute(
        "UPDATE images SET features_json = ? WHERE id = ?",
        (json.dumps(payload, sort_keys=True), image_id),
    )

    if status == STATUS_PROCESSED:
        connection.executemany(
            """
            INSERT INTO ripples (
                image_id, ripple_index, center_x, center_y,
                radius, width, height, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    image_id,
                    ripple.index,
                    ripple.center_x,
                    ripple.center_y,
                    ripple.radius,
                    ripple.width,
                    ripple.height,
                    ripple.confidence,
                )
                for ripple in attributes.ripples
            ],
        )
    connection.commit()
    return image_id


def load_image(
    connection: sqlite3.Connection, image_id: int
) -> RippleAttributes | None:
    """Load the attribute document of ``image_id`` (``None`` when absent)."""
    row = connection.execute(
        "SELECT features_json FROM images WHERE id = ?", (image_id,)
    ).fetchone()
    if row is None:
        return None
    payload: dict[str, Any] = json.loads(row["features_json"])
    payload["image_id"] = int(image_id)
    return RippleAttributes.from_dict(payload)


def list_image_ids(connection: sqlite3.Connection) -> list[int]:
    """Return the ids of every stored image, oldest first."""
    rows = connection.execute("SELECT id FROM images ORDER BY id").fetchall()
    return [int(row["id"]) for row in rows]


def count_images(connection: sqlite3.Connection) -> int:
    """Return the number of stored images."""
    row = connection.execute("SELECT COUNT(*) AS total FROM images").fetchone()
    return int(row["total"])


def store_master_key(
    connection: sqlite3.Connection,
    master_key: MasterKey,
) -> int:
    """Insert a master key and return its database id."""
    cursor = connection.execute(
        """
        INSERT INTO master_keys (
            image_id, master_key, bits, algorithm, parameters_json, derived_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            master_key.image_id,
            master_key.key,
            master_key.bits,
            master_key.algorithm,
            json.dumps(master_key.parameters, sort_keys=True),
            master_key.derived_at,
        ),
    )
    connection.commit()
    return int(cursor.lastrowid or 0)


def store_slave_key(connection: sqlite3.Connection, slave_key: SlaveKey) -> int:
    """Insert a slave key and return its database id."""
    cursor = connection.execute(
        """
        INSERT INTO slave_keys (
            master_key_id, image_id, ripple_index,
            slave_key, bits, algorithm, derived_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            slave_key.master_key_id,
            slave_key.image_id,
            slave_key.ripple_index,
            slave_key.key,
            slave_key.bits,
            slave_key.algorithm,
            slave_key.derived_at,
        ),
    )
    connection.commit()
    return int(cursor.lastrowid or 0)


def load_master_key(
    connection: sqlite3.Connection, master_key_id: int
) -> MasterKey | None:
    """Load a master key by id (``None`` when absent)."""
    row = connection.execute(
        "SELECT * FROM master_keys WHERE id = ?", (master_key_id,)
    ).fetchone()
    if row is None:
        return None
    return MasterKey(
        image_id=int(row["image_id"]),
        key=str(row["master_key"]),
        bits=int(row["bits"]),
        algorithm=str(row["algorithm"]),
        parameters=json.loads(row["parameters_json"]),
        derived_at=str(row["derived_at"]),
    )


def find_master_key_for_image(
    connection: sqlite3.Connection, image_id: int
) -> MasterKey | None:
    """Load the master key that belongs to ``image_id`` (``None`` when absent)."""
    row = connection.execute(
        "SELECT id FROM master_keys WHERE image_id = ?", (image_id,)
    ).fetchone()
    if row is None:
        return None
    return load_master_key(connection, int(row["id"]))


def delete_master_key_for_image(connection: sqlite3.Connection, image_id: int) -> int:
    """Delete the master key of ``image_id`` (and its slave keys).

    Returns:
        The number of deleted master key rows.
    """
    cursor = connection.execute(
        "DELETE FROM master_keys WHERE image_id = ?", (image_id,)
    )
    connection.commit()
    return cursor.rowcount


def list_slave_keys(
    connection: sqlite3.Connection, master_key_id: int
) -> list[SlaveKey]:
    """Return every slave key that belongs to ``master_key_id``."""
    rows = connection.execute(
        "SELECT * FROM slave_keys WHERE master_key_id = ? ORDER BY ripple_index",
        (master_key_id,),
    ).fetchall()
    return [
        SlaveKey(
            master_key_id=int(row["master_key_id"]),
            image_id=int(row["image_id"]),
            ripple_index=int(row["ripple_index"]),
            key=str(row["slave_key"]),
            bits=int(row["bits"]),
            algorithm=str(row["algorithm"]),
            derived_at=str(row["derived_at"]),
        )
        for row in rows
    ]


def load_ripples(
    connection: sqlite3.Connection, image_id: int
) -> list[RippleDetection]:
    """Return the ripple rows stored for ``image_id``."""
    rows = connection.execute(
        "SELECT * FROM ripples WHERE image_id = ? ORDER BY ripple_index",
        (image_id,),
    ).fetchall()
    return [
        RippleDetection(
            index=int(row["ripple_index"]),
            center_x=float(row["center_x"]),
            center_y=float(row["center_y"]),
            radius=float(row["radius"]),
            width=float(row["width"]),
            height=float(row["height"]),
            confidence=float(row["confidence"]),
        )
        for row in rows
    ]
