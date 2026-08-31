# Simple JSON-backed kill/death counters, one entry per player UUID.
# Nothing fancy - loads once on enable, saves right after every change.

import json
from pathlib import Path
from typing import Dict


class StatsStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: Dict[str, Dict[str, int]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._data = json.loads(self._path.read_text())
        except (OSError, ValueError):
            # Corrupt or unreadable file - start fresh rather than crash the plugin.
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    def _entry(self, player_id: str) -> Dict[str, int]:
        return self._data.setdefault(player_id, {"kills": 0, "deaths": 0})

    def kills(self, player_id: str) -> int:
        return self._entry(player_id)["kills"]

    def deaths(self, player_id: str) -> int:
        return self._entry(player_id)["deaths"]

    def add_kill(self, player_id: str) -> None:
        self._entry(player_id)["kills"] += 1
        self._save()

    def add_death(self, player_id: str) -> None:
        self._entry(player_id)["deaths"] += 1
        self._save()
