"""Tests for the declarative data model catalogue.

The catalogue in :mod:`rainrs_server.model.schema` must describe the
dataclasses of the package exactly; these tests make sure that it
cannot drift away from them.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass

import pytest

from rainrs_server.model import schema
from rainrs_server.model.detection import (
    DetectionResult,
    RippleAttributes,
    RippleDetection,
)
from rainrs_server.model.keys import MasterKey, SlaveKey
from rainrs_server.model.outcome import ImageOutcome
from rainrs_server.model.state import RippleWaveParameters

MODEL_CLASSES = (
    RippleDetection,
    DetectionResult,
    RippleAttributes,
    ImageOutcome,
    MasterKey,
    SlaveKey,
    RippleWaveParameters,
)


def test_catalogue_matches_the_dataclasses() -> None:
    """The catalogue describes every entity without a difference."""
    assert schema.verify() == []


def test_every_dataclass_is_documented() -> None:
    """Every dataclass of the model package appears in the catalogue."""
    documented = {entry.name for entry in schema.entities()}

    for cls in MODEL_CLASSES:
        assert cls.__name__ in documented
        assert is_dataclass(cls)
        assert schema.ENTITY_CLASSES[cls.__name__] is cls


def test_entity_lookup() -> None:
    """The entity catalogue can be looked up by name."""
    entry = schema.entity("RippleAttributes")

    assert entry.table == "images"
    assert entry.field_names()[0] == "source_path"
    assert schema.fields_of("MasterKey")[0].name == "image_id"

    with pytest.raises(KeyError):
        schema.entity("NoSuchEntity")


def test_field_rows_cover_every_field() -> None:
    """The flat rows of the catalogue cover every documented field."""
    rows = schema.field_rows()
    expected = sum(len(entry.fields) for entry in schema.entities())

    assert len(rows) == expected
    assert all(len(row) == 6 for row in rows)
    assert {row[0] for row in rows} == {entry.name for entry in schema.entities()}


def test_render_markdown_mentions_every_entity() -> None:
    """The Markdown rendering of the catalogue names every entity."""
    document = schema.render_markdown()

    for entry in schema.entities():
        assert entry.name in document
        for item in entry.fields:
            assert item.name in document


def test_nullable_fields_are_marked() -> None:
    """The catalogue marks the fields that may be ``None``."""
    optional = {
        (entry.name, item.name)
        for entry in schema.entities()
        for item in entry.fields
        if item.nullable
    }

    assert ("RippleAttributes", "image_id") in optional
    assert ("RippleAttributes", "stored_path") in optional
    assert ("RippleAttributes", "source_path") not in optional
    assert ("MasterKey", "key") not in optional


def test_dataclass_fields_are_typed_as_documented() -> None:
    """The documented type of a field is the type of the dataclass."""
    for entry in schema.entities():
        cls = schema.ENTITY_CLASSES[entry.name]
        declared = {item.name: item.type for item in fields(cls)}
        for item in entry.fields:
            assert declared[item.name] == item.type
