"""Atomic file writes for state the tool (or a reader) depends on.

Every file that another read interprets — the rollback store, the staging
transaction, the watch baseline, the KB override, the journal cache — is
replaced whole (write to a sibling temp file, then os.replace). A crash or
a full disk can no longer leave a half-written file that a later read
silently misinterprets: os.replace is atomic on POSIX, and the worst case
is the previous generation of the file, which was valid.

The state directory keeps no stray *.tmp* siblings: a failed attempt is
removed before the exception is re-raised.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Replace `path` with `text` atomically (temp sibling + os.replace)."""
    _atomic(path, text.encode(encoding))


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Replace `path` with `data` atomically (temp sibling + os.replace)."""
    _atomic(path, data)


def _atomic(path: Path, data: bytes) -> None:
    p = Path(path)
    parent = p.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(parent), prefix=f".{p.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
