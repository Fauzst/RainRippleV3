"""The JSON attribute documents of the processed captures.

For every processed capture the pipeline writes one JSON document that
holds the extracted attributes. The document is the serialised form of
:class:`~rainrs_server.model.detection.RippleAttributes`; it is written
with sorted keys so that two runs over the same capture produce byte
identical documents.

The documents live in ``storage/features`` and are excluded from version
control: they contain derived features.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..model.detection import RippleAttributes

logger = logging.getLogger(__name__)

__all__ = ["AttributeWriter"]


class AttributeWriter:
    """Writes one JSON attribute document per processed capture.

    Args:
        features_dir: Directory the documents are written to.
    """

    def __init__(self, features_dir: Path) -> None:
        self._features_dir = Path(features_dir)

    @property
    def features_dir(self) -> Path:
        """The directory the attribute documents are written to."""
        return self._features_dir

    def write(self, attributes: RippleAttributes) -> Path:
        """Write the attribute document of ``attributes``.

        Args:
            attributes: The extracted attributes of one capture.

        Returns:
            The path of the written document.
        """
        self._features_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(attributes.source_path).stem
        target = self._features_dir / f"{stem}.json"
        target.write_text(
            json.dumps(attributes.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        logger.info("wrote attribute document %s", target.name)
        return target
