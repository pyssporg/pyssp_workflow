"""Output directory helpers shared by the authoring build steps."""

from __future__ import annotations

import shutil
from pathlib import Path


def reset_dir(path: Path) -> None:
    """Remove ``path`` if it exists and recreate it empty."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


__all__ = ["reset_dir"]
