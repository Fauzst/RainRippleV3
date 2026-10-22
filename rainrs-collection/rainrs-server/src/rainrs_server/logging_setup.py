"""Logging configuration for the server pipeline.

The pipeline writes a rotating log file to ``logs/rainrs.log`` (the
directory is derived from :class:`rainrs_server.config.ServerPaths`).
Every module obtains its logger through :func:`get_logger`, so all
records share one format and one destination.

Security note
-------------
The pipeline logs **never** contain captured images, derived ripple
features or generated key material. Only metadata such as file names,
detection counts, statuses and timings are recorded. Feature values and
keys are printed by :func:`rainrs_server.process.dev.dev_print` instead,
which is development-only and stdout-bound.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

from .config import ENV_LOG_LEVEL, ServerPaths

LOG_FILE_NAME = "rainrs.log"
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5

_configured = False


def get_logger(name: str) -> logging.Logger:
    """Return the logger for ``name`` (usually ``__name__``)."""
    return logging.getLogger(name)


def configure_logging(
    logs_dir: Path | None = None,
    *,
    level: int | str | None = None,
    console: bool = False,
    force: bool = False,
) -> logging.Logger:
    """Configure the root ``rainrs_server`` logger.

    Args:
        logs_dir: Directory for the log file. Defaults to the ``logs``
            directory of the detected server root.
        level: Logging level. Defaults to ``RAINRS_LOG_LEVEL`` or
            ``INFO``.
        console: Also attach a stderr handler. Off by default so that
            the CLI output stays machine readable.
        force: Reconfigure even if logging was already set up.

    Returns:
        The configured ``rainrs_server`` logger.
    """
    global _configured
    root_logger = logging.getLogger("rainrs_server")
    if _configured and not force:
        return root_logger

    if logs_dir is None:
        logs_dir = ServerPaths.from_root().logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)

    resolved_level = (
        level if level is not None else os.environ.get(ENV_LOG_LEVEL, "INFO")
    )
    if isinstance(resolved_level, str):
        resolved_level = logging.getLevelNamesMapping().get(
            resolved_level.upper(), logging.INFO
        )

    root_logger.setLevel(resolved_level)
    root_logger.propagate = False
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / LOG_FILE_NAME,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(resolved_level)
    root_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(resolved_level)
        root_logger.addHandler(console_handler)

    _configured = True
    return root_logger
