"""Filesystem layout and runtime settings for ``rainrs-server``.

The server is executed from a checkout of the ``rainrs-server``
application directory, which is expected to contain:

```
rainrs-server/
  pyproject.toml
  src/rainrs_server/
  model/content/runs/detect/rain_ripple_yolo26_cpu/weights/best.pt
  storage/
    images/raw/        # incoming captures
    images/processed/  # captures whose features were extracted
    features/          # JSON attribute documents
  logs/                # pipeline logs
```

All paths are derived from a single *server root* so that every module
(the detector, the database layer and the CLI) agrees on where data
lives.  The root can be overridden with the ``RAINRS_HOME``
environment variable, which is useful for tests and for running the
package from an installed location.

Environment variables
---------------------
``RAINRS_HOME``
    Overrides the detected server root.
``RAINRS_DEV_PRINT``
    Enables the development-only console printing (see
    :mod:`rainrs_server.process.dev`).
``RAINRS_LOG_LEVEL``
    Logging level for the pipeline log file (``DEBUG`` … ``CRITICAL``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_HOME = "RAINRS_HOME"
ENV_LOG_LEVEL = "RAINRS_LOG_LEVEL"

#: Detector defaults. ``imgsz`` matches the size the model was trained on
#: (``model/content/runs/detect/rain_ripple_yolo26_cpu/args.yaml``).
DEFAULT_CONF = 0.25
DEFAULT_IOU = 0.7
DEFAULT_IMGSZ = 416
DEFAULT_DEVICE = "cpu"

#: Research key sizes (bits). The project targets 32–64 bit experimental
#: artifacts; the values are *not* suitable for production keys.
ALLOWED_KEY_BITS = (32, 64)
DEFAULT_KEY_BITS = 64

#: Image file extensions handled by the capture pipeline.
SUPPORTED_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")


def find_server_root() -> Path:
    """Return the root directory of the ``rainrs-server`` application.

    Resolution order:

    1. the ``RAINRS_HOME`` environment variable, when set;
    2. the closest ancestor of this module that contains both
       ``pyproject.toml`` and ``src/rainrs_server``;
    3. the current working directory as a last resort.
    """
    override = os.environ.get(ENV_HOME)
    if override:
        return Path(override).expanduser().resolve()

    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "rainrs_server"
        ).is_dir():
            return candidate
    return Path.cwd()


@dataclass(frozen=True, slots=True)
class ServerPaths:
    """Absolute locations of every file and directory the server uses."""

    root: Path
    storage_dir: Path
    raw_images_dir: Path
    processed_images_dir: Path
    features_dir: Path
    logs_dir: Path
    model_weights: Path
    database: Path

    @classmethod
    def from_root(cls, root: Path | None = None) -> ServerPaths:
        """Build the path set for ``root`` (defaults to :func:`find_server_root`)."""
        base = (root or find_server_root()).resolve()
        storage = base / "storage"
        return cls(
            root=base,
            storage_dir=storage,
            raw_images_dir=storage / "images" / "raw",
            processed_images_dir=storage / "images" / "processed",
            features_dir=storage / "features",
            logs_dir=base / "logs",
            model_weights=(
                base
                / "model"
                / "content"
                / "runs"
                / "detect"
                / "rain_ripple_yolo26_cpu"
                / "weights"
                / "best.pt"
            ),
            database=storage / "rainrs.db",
        )

    def ensure_directories(self) -> None:
        """Create the writable directories used by the pipeline."""
        for directory in (
            self.storage_dir,
            self.raw_images_dir,
            self.processed_images_dir,
            self.features_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class DetectionSettings:
    """Tunables for the YOLO26 rain-ripple detector."""

    conf: float = DEFAULT_CONF
    iou: float = DEFAULT_IOU
    imgsz: int = DEFAULT_IMGSZ
    device: str = DEFAULT_DEVICE

    def validated(self) -> DetectionSettings:
        """Return the settings after range checking, raising ``ValueError``."""
        if not 0.0 < self.conf <= 1.0:
            raise ValueError(f"confidence must be in (0, 1], got {self.conf}")
        if not 0.0 < self.iou <= 1.0:
            raise ValueError(f"IoU must be in (0, 1], got {self.iou}")
        if self.imgsz <= 0:
            raise ValueError(f"imgsz must be positive, got {self.imgsz}")
        if not self.device:
            raise ValueError("device must not be empty")
        return self


def resolve_key_bits(bits: int) -> int:
    """Validate a research key size in bits (32 or 64)."""
    if bits not in ALLOWED_KEY_BITS:
        raise ValueError(f"key size must be one of {ALLOWED_KEY_BITS} bits, got {bits}")
    return bits
