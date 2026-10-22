"""The incoming captures and the lifecycle of their files.

The capture library is the *input* layer of the pipeline. It knows

* which files of the raw directory are captures the pipeline handles
  (:func:`is_supported_image`),
* which captures are waiting to be processed
  (:meth:`CaptureLibrary.list_captures`),
* where a capture is archived once its features were stored
  (:meth:`CaptureLibrary.destination_for` and
  :meth:`CaptureLibrary.archive`), and
* that a capture without a measurable ripple is removed
  (:meth:`CaptureLibrary.discard`).

The layer deliberately knows nothing about detection or about key
derivation: it only moves files around, so that the process layer can
stay free of filesystem concerns.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from ..config import SUPPORTED_IMAGE_SUFFIXES

logger = logging.getLogger(__name__)

__all__ = ["CaptureLibrary", "is_supported_image"]


def is_supported_image(path: Path) -> bool:
    """Return ``True`` when ``path`` looks like a supported image file."""
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_SUFFIXES


class CaptureLibrary:
    """The raw capture directory and the lifecycle of the files in it.

    Args:
        raw_dir: Directory holding the incoming captures.
        processed_dir: Directory the captures are moved to once their
            features were extracted.
    """

    def __init__(self, *, raw_dir: Path, processed_dir: Path) -> None:
        self._raw_dir = Path(raw_dir)
        self._processed_dir = Path(processed_dir)

    @property
    def raw_dir(self) -> Path:
        """The directory the incoming captures are read from."""
        return self._raw_dir

    @property
    def processed_dir(self) -> Path:
        """The directory the processed captures are moved to."""
        return self._processed_dir

    def list_captures(self, directory: Path | None = None) -> list[Path]:
        """Return every supported capture, in file-name order.

        Args:
            directory: Directory to scan. Defaults to the raw capture
                directory of this library.

        Returns:
            The supported image files of the directory. An empty list is
            returned when the directory does not exist.
        """
        target = Path(directory) if directory is not None else self._raw_dir
        if not target.is_dir():
            logger.error("capture directory not found: %s", target)
            return []
        captures = sorted(
            path
            for path in target.iterdir()
            if path.is_file() and is_supported_image(path)
        )
        logger.info("found %d capture(s) in %s", len(captures), target)
        return captures

    def destination_for(self, image_path: Path) -> Path:
        """Return the path the capture will be archived to.

        The processed directory is created when it does not exist yet.
        The returned path does not exist, so that an existing capture is
        never overwritten.
        """
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        return _unique_destination(self._processed_dir / Path(image_path).name)

    def archive(self, image_path: Path) -> Path:
        """Move the capture from the raw directory to the processed one.

        Returns:
            The path the capture was moved to.
        """
        image_path = Path(image_path)
        destination = self.destination_for(image_path)
        shutil.move(str(image_path), str(destination))
        logger.info("moved capture to %s", destination.name)
        return destination

    def discard(self, image_path: Path) -> None:
        """Delete the capture because it carries no measurable ripple."""
        image_path = Path(image_path)
        try:
            image_path.unlink()
        except FileNotFoundError:
            logger.warning("capture %s was already gone", image_path.name)
            return
        logger.info("deleted capture %s", image_path.name)


def _unique_destination(destination: Path) -> Path:
    """Return a path that does not exist yet, adding a numeric suffix."""
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    counter = 1
    candidate = destination.with_name(f"{stem}_{counter}{suffix}")
    while candidate.exists():
        counter += 1
        candidate = destination.with_name(f"{stem}_{counter}{suffix}")
    return candidate
