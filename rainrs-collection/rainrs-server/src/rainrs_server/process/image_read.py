"""Rain-ripple feature extraction with the trained YOLO26 detector.

The extraction stage is the *process* layer of the pipeline: it takes a
capture from the input layer, measures it and hands the result to the
output layer.

Inputs
------
* One captured image file (JPEG, PNG, …) taken from the raw capture
  directory (``storage/images/raw``), provided by
  :class:`~rainrs_server.input.captures.CaptureLibrary`.
* The trained detector weights
  ``model/content/runs/detect/rain_ripple_yolo26_cpu/weights/best.pt``
  (Ultralytics checkpoint, trained for 416 px inputs on CPU).

Outputs
-------
* :class:`~rainrs_server.model.detection.RippleAttributes` — for every
  detected ripple the centre position and the radius, plus the number of
  ripples.
* A JSON attribute document written by
  :class:`~rainrs_server.output.attributes.AttributeWriter` to
  ``storage/features/<name>.json``.
* Rows in the ``images`` and ``ripples`` tables of the SQLite database.
* The capture is moved from ``storage/images/raw`` to
  ``storage/images/processed`` once its features were stored. When the
  detector finds no ripple at all, the capture is deleted instead.

Behaviour
---------
Every image is processed independently: an error on one capture is
logged and the batch continues with the next file. Failed captures stay
in the raw directory so that they can be retried.

The module never writes derived features or key material to the log
files; development output goes through
:func:`rainrs_server.process.dev.dev_print` instead.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ultralytics.engine.results import Results

from ..config import DetectionSettings
from ..input.captures import CaptureLibrary, is_supported_image
from ..model.base import utc_now_iso
from ..model.detection import DetectionResult, RippleAttributes, RippleDetection
from ..model.outcome import (
    STATUS_ERROR,
    STATUS_NO_FEATURES,
    STATUS_PROCESSED,
    ImageOutcome,
)
from ..output.attributes import AttributeWriter
from ..output.database import open_database, store_image
from .dev import dev_print

logger = logging.getLogger(__name__)

__all__ = [
    "RainRippleDetector",
    "RippleDetector",
    "RippleFeatureExtractor",
    "is_supported_image",
    "process_directory",
    "process_image",
    "utc_now_iso",
]


class RippleDetector(Protocol):
    """Protocol implemented by the detector used by the extractor.

    The extractor only needs a single method, which keeps the pipeline
    testable without loading the neural network: tests inject a stub
    detector that returns fixed detections.
    """

    def detect(self, image_path: Path) -> DetectionResult:
        """Return the detections for ``image_path``."""


class RainRippleDetector:
    """Ultralytics YOLO26 rain-ripple detector.

    The model is loaded once and reused for every image. Inference runs
    on the CPU by default, matching the ``rain_ripple_yolo26_cpu``
    training run; a CUDA device can be requested through
    ``DetectionSettings.device``.

    Args:
        weights_path: Path to the Ultralytics ``best.pt`` checkpoint.
        settings: Detection thresholds and image size.
    """

    def __init__(
        self,
        weights_path: Path,
        *,
        settings: DetectionSettings | None = None,
    ) -> None:
        self._weights_path = Path(weights_path)
        self._settings = (settings or DetectionSettings()).validated()
        if not self._weights_path.is_file():
            raise FileNotFoundError(f"detector weights not found: {self._weights_path}")

        # Imported lazily so that the rest of the package (and the test
        # suite) can be used without pulling in torch.
        from ultralytics import YOLO

        logger.info("loading detector weights from %s", self._weights_path.name)
        self._model = YOLO(str(self._weights_path))
        names = getattr(self._model, "names", None)
        if names:
            dev_print("detector classes: %s", names)

    @property
    def settings(self) -> DetectionSettings:
        """The detection settings in use."""
        return self._settings

    def detect(self, image_path: Path) -> DetectionResult:
        """Run the detector on ``image_path``.

        Returns:
            The detections in original-image pixel coordinates.

        Raises:
            FileNotFoundError: The image does not exist.
            RuntimeError: The detector returned no result object.
        """
        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"image not found: {image_path}")

        predictions = self._model.predict(
            source=str(image_path),
            conf=self._settings.conf,
            iou=self._settings.iou,
            imgsz=self._settings.imgsz,
            device=self._settings.device,
            verbose=False,
        )
        results = [cast("Results", item) for item in predictions]
        if not results:
            raise RuntimeError(f"detector returned no result for {image_path.name}")

        result = results[0]
        height, width = result.orig_shape
        ripples: list[RippleDetection] = []
        boxes = getattr(result, "boxes", None)
        if boxes is not None and len(boxes):
            coordinates = boxes.xywh.tolist()
            confidences = boxes.conf.tolist()
            for index, (center_x, center_y, box_width, box_height) in enumerate(
                coordinates
            ):
                confidence = float(confidences[index])
                ripples.append(
                    RippleDetection(
                        index=index,
                        center_x=float(center_x),
                        center_y=float(center_y),
                        radius=(float(box_width) + float(box_height)) / 4.0,
                        width=float(box_width),
                        height=float(box_height),
                        confidence=confidence,
                    )
                )

        return DetectionResult(
            image_width=int(width),
            image_height=int(height),
            ripples=tuple(ripples),
        )


class RippleFeatureExtractor:
    """Turn captured images into stored rain-ripple attributes.

    The extractor joins the three layers of the application: it reads
    the captures from the input layer, measures them and writes the
    result through the output layer.

    Args:
        detector: The detector to run (see :class:`RippleDetector`).
        database_path: SQLite database holding the extracted features.
        captures: The capture library the captures are read from and
            archived in.
        writer: The writer of the JSON attribute documents.
        move_images: Set to ``False`` to keep the captures in place
            (useful for dry runs).
        delete_without_features: Set to ``False`` to keep captures for
            which no ripple was detected.
    """

    def __init__(
        self,
        *,
        detector: RippleDetector,
        database_path: Path,
        captures: CaptureLibrary,
        writer: AttributeWriter,
        move_images: bool = True,
        delete_without_features: bool = True,
    ) -> None:
        self._detector = detector
        self._database_path = Path(database_path)
        self._captures = captures
        self._writer = writer
        self._move_images = move_images
        self._delete_without_features = delete_without_features

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, image_path: Path) -> RippleAttributes:
        """Run the detector and return the extracted attributes.

        No side effects are performed: nothing is written to disk or to
        the database.
        """
        image_path = Path(image_path)
        result = self._detector.detect(image_path)
        return RippleAttributes(
            source_path=str(image_path),
            image_width=result.image_width,
            image_height=result.image_height,
            detected_at=utc_now_iso(),
            ripples=result.ripples,
        )

    def process_image(self, image_path: Path) -> ImageOutcome:
        """Process a single capture end to end.

        The attributes are stored in the database and as a JSON document
        *before* the capture is moved, so a failure can never lose data.
        """
        image_path = Path(image_path)
        logger.info("processing capture %s", image_path.name)

        try:
            attributes = self.extract(image_path)
        except Exception as exc:  # noqa: BLE001 - one capture must not abort the batch
            logger.error("detection failed for %s: %s", image_path.name, exc)
            dev_print("detection failed for %s: %s", image_path.name, exc)
            self._record_error(image_path, exc)
            return ImageOutcome(
                source=str(image_path),
                status=STATUS_ERROR,
                error=str(exc),
            )

        if not attributes.ripples:
            logger.warning(
                "no ripple detected in %s - capture discarded", image_path.name
            )
            dev_print("no ripple detected in %s - capture discarded", image_path.name)
            image_id = self._store(attributes, status=STATUS_NO_FEATURES)
            if self._delete_without_features:
                self._captures.discard(image_path)
            return ImageOutcome(
                source=str(image_path),
                status=STATUS_NO_FEATURES,
                image_id=image_id,
                ripple_count=0,
            )

        destination = (
            self._captures.destination_for(image_path) if self._move_images else None
        )
        located = attributes.with_storage(
            stored_path=str(destination) if destination else None
        )
        image_id = self._store(located, status=STATUS_PROCESSED)
        located = located.with_storage(image_id=image_id)
        features_path = self._writer.write(located)

        if destination is not None:
            stored_path = self._captures.archive(image_path)
            located = located.with_storage(stored_path=str(stored_path))

        logger.info("extracted %d ripple(s) from %s", attributes.count, image_path.name)
        dev_print(
            "%s -> %d ripple(s) (image_id=%s)",
            image_path.name,
            attributes.count,
            image_id,
        )
        return ImageOutcome(
            source=str(image_path),
            status=STATUS_PROCESSED,
            image_id=image_id,
            ripple_count=attributes.count,
            features_path=str(features_path),
            stored_path=located.stored_path,
        )

    def process_directory(self, directory: Path | None = None) -> list[ImageOutcome]:
        """Process every supported image in ``directory``.

        Args:
            directory: Directory to scan. Defaults to the raw capture
                directory of the capture library.

        Returns:
            One :class:`ImageOutcome` per image, in file-name order.
        """
        images = self._captures.list_captures(directory)

        outcomes: list[ImageOutcome] = []
        for image_path in images:
            outcomes.append(self.process_image(image_path))
        return outcomes

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _store(self, attributes: RippleAttributes, *, status: str) -> int:
        with open_database(self._database_path) as connection:
            return store_image(connection, attributes, status=status)

    def _record_error(self, image_path: Path, error: Exception) -> None:
        attributes = RippleAttributes(
            source_path=str(image_path),
            image_width=0,
            image_height=0,
            detected_at=utc_now_iso(),
        )
        try:
            with open_database(self._database_path) as connection:
                store_image(
                    connection, attributes, status=STATUS_ERROR, error=str(error)
                )
        except (
            Exception
        ):  # pragma: no cover - defensive, database must not break the run
            logger.exception("could not record the failure of %s", image_path.name)


def process_image(
    image_path: Path,
    *,
    extractor: RippleFeatureExtractor,
) -> ImageOutcome:
    """Process a single capture with ``extractor`` (functional wrapper)."""
    return extractor.process_image(Path(image_path))


def process_directory(
    directory: Path | None = None,
    *,
    extractor: RippleFeatureExtractor,
) -> list[ImageOutcome]:
    """Process a directory of captures with ``extractor`` (wrapper)."""
    return extractor.process_directory(directory)
