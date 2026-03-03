"""
title: Base classes for ArtBox.
"""

from __future__ import annotations

from abc import ABC
from pathlib import Path


class ArtBox(ABC):
    """
    title: The base class for all ArtBox classes.
    """

    def __init__(self, args: dict[str, str]) -> None:
        """
        title: Initialize ArtBox class.
        parameters:
          args:
            type: dict[str, str]
        """
        self.args: dict[str, str] = args
        self.input_path = Path(self.args.get("input-path", "/tmp"))
        self.output_path = Path(self.args.get("output-path", "/tmp"))
