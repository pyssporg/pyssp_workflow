"""Subprocess helpers shared by the authoring build steps."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def find_executable(
    name: str,
    explicit: str | Path | None,
    *,
    hint: str,
    env_var: str | None = None,
) -> str:
    """Resolve ``name``, preferring ``explicit``, ``env_var``, a sibling, PATH."""
    if explicit is not None:
        return str(explicit)
    if env_var is not None:
        configured = os.environ.get(env_var)
        if configured:
            return configured
    sibling = Path(sys.executable).with_name(name)
    if sibling.is_file():
        return str(sibling)
    found = shutil.which(name)
    if found is None:
        raise FileNotFoundError(f"{name} executable not found; {hint}")
    return found


def run(
    command: Sequence[str],
    *,
    timeout: float,
    cwd: Path | str | None = None,
) -> str:
    """Run ``command`` and return stdout; raise ``RuntimeError`` on failure."""
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{' '.join(command)} failed with exit code {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout


__all__ = ["find_executable", "run"]
