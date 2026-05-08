#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""milfological — cRPG asset generation pipeline."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("milfological")
except PackageNotFoundError:
    __version__ = "0.1.0-dev"

__all__ = ["auto_caption", "entity_cutout", "entity_pixelart", "protocols", "backends"]
