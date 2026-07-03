"""Cross-process reservation ID handoff for the CLI + workload examples."""

from __future__ import annotations

from pathlib import Path

_STATE_FILE = Path(__file__).with_name(".current_reservation_id")


def write_reservation_id(reservation_id: str) -> Path:
    """Write a reservation id for other processes to pick up."""
    _STATE_FILE.write_text(reservation_id, encoding="utf-8")
    return _STATE_FILE


def clear_reservation_id() -> None:
    """Remove the stored reservation id."""
    _STATE_FILE.unlink(missing_ok=True)


def read_reservation_id() -> str | None:
    """Read a reservation id from the example state file."""
    if _STATE_FILE.is_file():
        return _STATE_FILE.read_text(encoding="utf-8").strip() or None
    return None
