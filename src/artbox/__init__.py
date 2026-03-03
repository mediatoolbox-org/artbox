"""
title: GGPEDIA Youtube.
"""
# mypy: disable-error-code="attr-defined"

from importlib import metadata as importlib_metadata


def get_version():
    """
    title: Return the program version.
    """
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "0.12.0"  # semantic-release


version = get_version()

__version__ = version
__author__ = "Ivan Ogasawara"
__email__ = "ivan.ogasawara@gmail.com"
