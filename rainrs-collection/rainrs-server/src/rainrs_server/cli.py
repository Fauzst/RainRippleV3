"""Command line interface of the rain-ripple capture processing pipeline.

Usage (run from the ``rainrs-server`` directory)::

    # Extract rain-ripple attributes with the trained YOLO26 detector
    uv run rainrs-server process --print
    uv run rainrs-server process --raw /path/to/raw --no-move

    # Derive master and slave keys from the stored attributes
    uv run rainrs-server derive --bits 64
    uv run rainrs-server derive --bits 32 --binding xor

    # Process the captures and derive the keys in one go
    uv run rainrs-server run --print

The heavy imports (``ultralytics``, ``torch``) happen inside the command
functions so that ``--help`` stays fast.

The commands only print counters; the derived key material itself is
written to the database and never printed unless the development
printing is switched on explicitly with ``--print``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import (
    DEFAULT_CONF,
    DEFAULT_DEVICE,
    DEFAULT_IMGSZ,
    DEFAULT_IOU,
    DetectionSettings,
    ServerPaths,
)
from .logging_setup import configure_logging
from .model.outcome import STATUS_ERROR, STATUS_NO_FEATURES, STATUS_PROCESSED
from .process.dev import ENV_DEV_PRINT


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rainrs-server",
        description="Rain Ripple Key Generator server pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser(
        "process",
        help="Extract rain-ripple attributes with the YOLO26 detector",
    )
    process.add_argument(
        "--raw", help="Raw capture directory (default: storage/images/raw)"
    )
    process.add_argument(
        "--processed", help="Processed directory (default: storage/images/processed)"
    )
    process.add_argument(
        "--features", help="Features directory (default: storage/features)"
    )
    process.add_argument(
        "--database", help="SQLite database (default: storage/rainrs.db)"
    )
    process.add_argument(
        "--weights", help="Detector weights (default: model/.../best.pt)"
    )
    process.add_argument(
        "--conf", type=float, default=DEFAULT_CONF, help="Confidence threshold"
    )
    process.add_argument(
        "--iou", type=float, default=DEFAULT_IOU, help="NMS IoU threshold"
    )
    process.add_argument(
        "--imgsz", type=int, default=DEFAULT_IMGSZ, help="Inference image size"
    )
    process.add_argument(
        "--device", default=DEFAULT_DEVICE, help="Device (cpu or cuda)"
    )
    process.add_argument(
        "--no-move", action="store_true", help="Do not move images to processed/"
    )
    process.add_argument(
        "--keep-no-features",
        action="store_true",
        help="Do not delete images for which no ripple was detected",
    )
    process.add_argument(
        "--print", action="store_true", help="Enable development console printing"
    )

    derive = subparsers.add_parser(
        "derive",
        help="Derive Runge-Kutta master/slave keys from stored attributes",
    )
    derive.add_argument(
        "--database", help="SQLite database (default: storage/rainrs.db)"
    )
    derive.add_argument(
        "--bits", type=int, default=64, choices=(32, 64), help="Key size in bits"
    )
    derive.add_argument(
        "--binding",
        choices=("hmac", "xor"),
        default="hmac",
        help="How the slave keys are bound to their master key",
    )
    derive.add_argument(
        "--overwrite", action="store_true", help="Re-derive existing keys"
    )
    derive.add_argument(
        "--image-id",
        type=int,
        action="append",
        help="Only derive for this image id (repeatable)",
    )
    derive.add_argument(
        "--print", action="store_true", help="Enable development console printing"
    )

    run_all = subparsers.add_parser(
        "run",
        help="Process the raw captures and derive the keys in one go",
    )
    run_all.add_argument(
        "--raw", help="Raw capture directory (default: storage/images/raw)"
    )
    run_all.add_argument("--bits", type=int, default=64, choices=(32, 64))
    run_all.add_argument("--binding", choices=("hmac", "xor"), default="hmac")
    run_all.add_argument("--print", action="store_true")

    return parser


def _enable_dev_print(enabled: bool) -> None:
    if enabled:
        os.environ[ENV_DEV_PRINT] = "1"


def cmd_process(args: argparse.Namespace) -> int:
    """Run the detection stage over the raw captures."""
    _enable_dev_print(bool(args.print))

    paths = ServerPaths.from_root()
    paths.ensure_directories()
    configure_logging(paths.logs_dir)

    raw_dir = Path(args.raw) if args.raw else paths.raw_images_dir
    processed_dir = (
        Path(args.processed) if args.processed else paths.processed_images_dir
    )
    features_dir = Path(args.features) if args.features else paths.features_dir
    database_path = Path(args.database) if args.database else paths.database
    weights_path = Path(args.weights) if args.weights else paths.model_weights

    settings = DetectionSettings(
        conf=args.conf, iou=args.iou, imgsz=args.imgsz, device=args.device
    ).validated()

    from .input.captures import CaptureLibrary
    from .output.attributes import AttributeWriter
    from .process.image_read import RainRippleDetector, RippleFeatureExtractor

    detector = RainRippleDetector(weights_path, settings=settings)
    extractor = RippleFeatureExtractor(
        detector=detector,
        database_path=database_path,
        captures=CaptureLibrary(raw_dir=raw_dir, processed_dir=processed_dir),
        writer=AttributeWriter(features_dir),
        move_images=not args.no_move,
        delete_without_features=not args.keep_no_features,
    )
    outcomes = extractor.process_directory(raw_dir)
    processed = [o for o in outcomes if o.status == STATUS_PROCESSED]
    no_features = [o for o in outcomes if o.status == STATUS_NO_FEATURES]
    errored = [o for o in outcomes if o.status == STATUS_ERROR]
    print(
        f"processed={len(processed)} "
        f"no_features={len(no_features)} "
        f"errors={len(errored)}"
    )
    return 0 if not errored else 1


def cmd_derive(args: argparse.Namespace) -> int:
    """Run the key derivation stage over the stored attributes."""
    _enable_dev_print(bool(args.print))

    paths = ServerPaths.from_root()
    paths.ensure_directories()
    configure_logging(paths.logs_dir)

    database_path = Path(args.database) if args.database else paths.database

    from .process.rungge import KeyDeriver

    deriver = KeyDeriver(
        database_path=database_path,
        bits=args.bits,
        binding=args.binding,
        overwrite=bool(args.overwrite),
    )
    derived = deriver.derive_for_all(args.image_id)
    print(f"derived_master_keys={len(derived)}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run the detection stage and the key derivation stage."""
    _enable_dev_print(bool(args.print))

    paths = ServerPaths.from_root()
    paths.ensure_directories()
    configure_logging(paths.logs_dir)

    process_args = argparse.Namespace(
        raw=args.raw,
        processed=None,
        features=None,
        database=None,
        weights=None,
        conf=DEFAULT_CONF,
        iou=DEFAULT_IOU,
        imgsz=DEFAULT_IMGSZ,
        device=DEFAULT_DEVICE,
        no_move=False,
        keep_no_features=False,
        print=args.print,
    )
    status = cmd_process(process_args)
    if status != 0:
        return status

    derive_args = argparse.Namespace(
        database=None,
        bits=args.bits,
        binding=args.binding,
        overwrite=False,
        image_id=None,
        print=args.print,
    )
    return cmd_derive(derive_args)


def main(argv: list[str] | None = None) -> int:
    """Entry point of the ``rainrs-server`` console script."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "process":
        return cmd_process(args)
    if args.command == "derive":
        return cmd_derive(args)
    if args.command == "run":
        return cmd_run(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
