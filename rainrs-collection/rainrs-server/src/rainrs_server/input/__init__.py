"""The input layer of the pipeline.

This layer owns everything that *enters* the application: the captured
images, their file names and their lifecycle on disk.

Modules
-------
``input.captures``
    The capture library: which files are picked up, where they are
    archived and when they are deleted.
"""

from __future__ import annotations

from .captures import CaptureLibrary, is_supported_image

__all__ = ["CaptureLibrary", "is_supported_image"]
