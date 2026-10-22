"""The data model of the rainrs-server pipeline.

Every value that flows through the application is described here:

======================  ====================================================
Module                  Contents
======================  ====================================================
``model.base``          Shared building blocks (JSON objects, timestamps).
``model.detection``     The measured geometry of the ripples.
``model.outcome``       The result of processing a single capture.
``model.keys``          The derived research artifacts.
``model.state``         The state of the Runge–Kutta integration.
``model.schema``        The catalogue of the shape of the data.
======================  ====================================================

The catalogue in :mod:`rainrs_server.model.schema` is the single
description of the shape of the data; it is verified against the
dataclasses of this package by the test suite.
"""

from __future__ import annotations

from .base import JsonObject, Serialisable, utc_now_iso
from .detection import DetectionResult, RippleAttributes, RippleDetection
from .keys import MasterKey, SlaveKey
from .outcome import (
    STATUS_ERROR,
    STATUS_NO_FEATURES,
    STATUS_PROCESSED,
    STATUS_VALUES,
    ImageOutcome,
)
from .schema import SCHEMA, Entity, Field, entities, entity, fields_of, verify
from .state import Derivative, RippleWaveParameters, Trajectory, Vector

__all__ = [
    "SCHEMA",
    "STATUS_ERROR",
    "STATUS_NO_FEATURES",
    "STATUS_PROCESSED",
    "STATUS_VALUES",
    "DetectionResult",
    "Derivative",
    "Entity",
    "Field",
    "ImageOutcome",
    "JsonObject",
    "MasterKey",
    "RippleAttributes",
    "RippleDetection",
    "RippleWaveParameters",
    "Serialisable",
    "SlaveKey",
    "Trajectory",
    "Vector",
    "entities",
    "entity",
    "fields_of",
    "utc_now_iso",
    "verify",
]
