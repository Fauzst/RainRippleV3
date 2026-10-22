"""The declarative shape of the data that flows through the pipeline.

This module is the *catalogue* of the data model: for every entity it
names the fields, their types and their meaning. It exists so that the
shape of the data can be read at a glance — in this file, in the
generated documentation, and in the tests — instead of being spread
over the dataclasses of the package.

The catalogue is not a copy that can drift away from the code:
:func:`verify` compares it against the dataclasses of
:mod:`rainrs_server.model` and reports every difference. The test suite
asserts that the report is empty, so a field that is added, renamed or
retyped without updating the catalogue fails the build.

Entities and their projections
------------------------------
============  ===================  =========================================
Entity        Stored in            Projection
============  ===================  =========================================
RippleDetection   ``ripples`` table    one row per detected ripple
DetectionResult   —                   transient detector output
RippleAttributes  ``images`` table    one row and one JSON document
ImageOutcome      —                   transient result of the pipeline
MasterKey         ``master_keys``      one row per capture
SlaveKey          ``slave_keys``       one row per detected ripple
RippleWaveParameters ``parameters_json`` part of the master key row
============  ===================  =========================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, is_dataclass
from typing import Any

from .detection import DetectionResult, RippleAttributes, RippleDetection
from .keys import MasterKey, SlaveKey
from .outcome import ImageOutcome
from .state import RippleWaveParameters

__all__ = [
    "ENTITY_CLASSES",
    "SCHEMA",
    "Entity",
    "Field",
    "entities",
    "entity",
    "field_rows",
    "fields_of",
    "render_markdown",
    "verify",
]


@dataclass(frozen=True, slots=True)
class Field:
    """One field of a data model entity.

    Attributes:
        name: The attribute name as it appears in the dataclass.
        type: The type of the attribute, written as it is written in the
            dataclass.
        description: What the field means.
        nullable: ``True`` when the field may be ``None``.
    """

    name: str
    type: str
    description: str
    nullable: bool = False


@dataclass(frozen=True, slots=True)
class Entity:
    """One entity of the data model.

    Attributes:
        name: The class name of the entity.
        description: What the entity describes.
        table: The SQLite table the entity is stored in, or ``None``
            when the entity is not persisted.
        fields: The fields of the entity.
    """

    name: str
    description: str
    table: str | None
    fields: tuple[Field, ...]

    def field_names(self) -> tuple[str, ...]:
        """Return the names of the fields, in declaration order."""
        return tuple(field.name for field in self.fields)


#: The catalogue of every entity of the data model.
SCHEMA: tuple[Entity, ...] = (
    Entity(
        name="RippleDetection",
        description="One rain ripple detected inside a captured image.",
        table="ripples",
        fields=(
            Field(
                "index",
                "int",
                "Zero-based position of the ripple inside its image.",
            ),
            Field(
                "center_x",
                "float",
                "Horizontal centre of the ripple, in pixels.",
            ),
            Field(
                "center_y",
                "float",
                "Vertical centre of the ripple, in pixels.",
            ),
            Field(
                "radius",
                "float",
                "Equivalent radius in pixels, (width + height) / 4.",
            ),
            Field(
                "width",
                "float",
                "Bounding-box width of the ripple, in pixels.",
            ),
            Field(
                "height",
                "float",
                "Bounding-box height of the ripple, in pixels.",
            ),
            Field(
                "confidence",
                "float",
                "Detector confidence, between 0.0 and 1.0.",
            ),
        ),
    ),
    Entity(
        name="DetectionResult",
        description="Raw detector output for a single image.",
        table=None,
        fields=(
            Field(
                "image_width",
                "int",
                "Width of the source image, in pixels.",
            ),
            Field(
                "image_height",
                "int",
                "Height of the source image, in pixels.",
            ),
            Field(
                "ripples",
                "tuple[RippleDetection, ...]",
                "The detected ripples, in detector order.",
            ),
        ),
    ),
    Entity(
        name="RippleAttributes",
        description=(
            "Every ripple measurement extracted from one captured image; "
            "the input of the Runge-Kutta key derivation."
        ),
        table="images",
        fields=(
            Field(
                "source_path",
                "str",
                "Path of the capture the attributes were extracted from.",
            ),
            Field(
                "image_width",
                "int",
                "Width of the source image, in pixels.",
            ),
            Field(
                "image_height",
                "int",
                "Height of the source image, in pixels.",
            ),
            Field(
                "detected_at",
                "str",
                "ISO 8601 UTC timestamp of the detection.",
            ),
            Field(
                "ripples",
                "tuple[RippleDetection, ...]",
                "Every ripple detected in the capture.",
            ),
            Field(
                "image_id",
                "int | None",
                "Identifier of the stored images row.",
                nullable=True,
            ),
            Field(
                "stored_path",
                "str | None",
                "Path the capture was moved to, when it was archived.",
                nullable=True,
            ),
        ),
    ),
    Entity(
        name="ImageOutcome",
        description="Result of processing a single capture.",
        table=None,
        fields=(
            Field(
                "source",
                "str",
                "Path of the capture that was processed.",
            ),
            Field(
                "status",
                "str",
                "One of processed, no_features or error.",
            ),
            Field(
                "image_id",
                "int | None",
                "Identifier of the stored images row.",
                nullable=True,
            ),
            Field(
                "ripple_count",
                "int",
                "Number of detected ripples.",
            ),
            Field(
                "features_path",
                "str | None",
                "Path of the JSON attribute document.",
                nullable=True,
            ),
            Field(
                "stored_path",
                "str | None",
                "Path the capture was moved to.",
                nullable=True,
            ),
            Field(
                "error",
                "str | None",
                "Error message; set only for the error status.",
                nullable=True,
            ),
        ),
    ),
    Entity(
        name="MasterKey",
        description=(
            "Experimental master key derived from the averaged ripple "
            "attributes of one capture."
        ),
        table="master_keys",
        fields=(
            Field(
                "image_id",
                "int",
                "Identifier of the capture the key belongs to.",
            ),
            Field(
                "key",
                "str",
                "Hex-encoded research artifact (not a production key).",
            ),
            Field(
                "bits",
                "int",
                "Size of the artifact in bits (32 or 64).",
            ),
            Field(
                "algorithm",
                "str",
                "Identifier of the derivation procedure.",
            ),
            Field(
                "parameters",
                "dict[str, float]",
                "Averaged attributes and ODE parameters used for the derivation.",
            ),
            Field(
                "derived_at",
                "str",
                "ISO 8601 UTC timestamp of the derivation.",
            ),
        ),
    ),
    Entity(
        name="SlaveKey",
        description=(
            "Experimental slave key, derived from a single ripple and "
            "bound to exactly one master key."
        ),
        table="slave_keys",
        fields=(
            Field(
                "master_key_id",
                "int",
                "Identifier of the master key this key belongs to.",
            ),
            Field(
                "image_id",
                "int",
                "Identifier of the capture the key belongs to.",
            ),
            Field(
                "ripple_index",
                "int",
                "Index of the ripple the key was derived from.",
            ),
            Field(
                "key",
                "str",
                "Hex-encoded research artifact (not a production key).",
            ),
            Field(
                "bits",
                "int",
                "Size of the artifact in bits (32 or 64).",
            ),
            Field(
                "algorithm",
                "str",
                "Identifier of the derivation procedure and of the binding.",
            ),
            Field(
                "derived_at",
                "str",
                "ISO 8601 UTC timestamp of the derivation.",
            ),
        ),
    ),
    Entity(
        name="RippleWaveParameters",
        description=(
            "Parameters of the coupled van der Pol oscillator system that "
            "the Runge-Kutta integration uses."
        ),
        table=None,
        fields=(
            Field(
                "mu",
                "float",
                "Nonlinearity (van der Pol damping) of both oscillators.",
            ),
            Field(
                "coupling",
                "float",
                "Coupling strength between the two oscillators.",
            ),
            Field(
                "forcing",
                "float",
                "Amplitude of the periodic forcing term.",
            ),
            Field(
                "phase",
                "float",
                "Phase of the forcing term, in radians.",
            ),
        ),
    ),
)

#: The dataclass behind every entity of the catalogue.
ENTITY_CLASSES: dict[str, type[Any]] = {
    "RippleDetection": RippleDetection,
    "DetectionResult": DetectionResult,
    "RippleAttributes": RippleAttributes,
    "ImageOutcome": ImageOutcome,
    "MasterKey": MasterKey,
    "SlaveKey": SlaveKey,
    "RippleWaveParameters": RippleWaveParameters,
}

_OPTIONAL = re.compile(r"Optional\[(.+)]")


def entities() -> tuple[Entity, ...]:
    """Return every entity of the catalogue."""
    return SCHEMA


def entity(name: str) -> Entity:
    """Return the entity called ``name``.

    Raises:
        KeyError: No entity of that name is described.
    """
    for entry in SCHEMA:
        if entry.name == name:
            return entry
    raise KeyError(f"unknown data model entity: {name}")


def fields_of(name: str) -> tuple[Field, ...]:
    """Return the fields of the entity called ``name``."""
    return entity(name).fields


def field_rows() -> list[tuple[str, str, str, str, bool, str]]:
    """Return the catalogue as flat rows for tabular rendering.

    Every row is ``(entity, table, field, type, nullable, description)``.
    """
    rows: list[tuple[str, str, str, str, bool, str]] = []
    for entry in SCHEMA:
        for field in entry.fields:
            rows.append(
                (
                    entry.name,
                    entry.table or "—",
                    field.name,
                    field.type,
                    field.nullable,
                    field.description,
                )
            )
    return rows


def _normalise(annotation: object) -> str:
    """Return a comparable form of a type annotation."""
    value = " ".join(str(annotation).split())
    match = _OPTIONAL.fullmatch(value)
    if match:
        return f"{match.group(1)} | None"
    return value


def verify() -> list[str]:
    """Return the differences between the catalogue and the dataclasses.

    An empty list means that the catalogue describes the data model
    exactly: every entity exists, every field is present with the
    declared type, and no field is undocumented.
    """
    problems: list[str] = []

    for entry in SCHEMA:
        cls = ENTITY_CLASSES.get(entry.name)
        if cls is None:
            problems.append(f"{entry.name}: the entity has no dataclass")
            continue
        if not is_dataclass(cls):
            problems.append(f"{entry.name}: the entity is not a dataclass")
            continue

        declared = {item.name: item.type for item in fields(cls)}
        documented = {item.name for item in entry.fields}

        for item in entry.fields:
            if item.name not in declared:
                problems.append(
                    f"{entry.name}.{item.name}: documented but missing in the dataclass"
                )
                continue
            if _normalise(declared[item.name]) != _normalise(item.type):
                problems.append(
                    f"{entry.name}.{item.name}: type {declared[item.name]!r} does "
                    f"not match the documented type {item.type!r}"
                )

        for name in sorted(set(declared) - documented):
            problems.append(
                f"{entry.name}.{name}: present in the dataclass but not documented"
            )

    for name in sorted(set(ENTITY_CLASSES) - {entry.name for entry in SCHEMA}):
        problems.append(f"{name}: the dataclass is not documented in the catalogue")

    return problems


def render_markdown() -> str:
    """Return the catalogue as a Markdown document."""
    lines: list[str] = ["# Data model", ""]
    for entry in SCHEMA:
        lines.append(f"## {entry.name}")
        lines.append("")
        lines.append(entry.description)
        lines.append("")
        lines.append("| Field | Type | Nullable | Description |")
        lines.append("| --- | --- | --- | --- |")
        for item in entry.fields:
            nullable = "yes" if item.nullable else "no"
            lines.append(
                f"| `{item.name}` | `{item.type}` | {nullable} | {item.description} |"
            )
        lines.append("")
    return "\n".join(lines)
