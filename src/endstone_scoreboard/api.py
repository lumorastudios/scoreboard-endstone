# Public API for other plugins to hook into the 

from typing import Callable, Dict

from endstone import Player

TagResolver = Callable[[Player], str]


class ScoreboardAPI:
    """Holds every registered tag and turns {tag} placeholders into text."""

    def __init__(self) -> None:
        self._tags: Dict[str, TagResolver] = {}

    def register_tag(self, name: str, resolver: TagResolver) -> None:
        """Register a placeholder. `name` is what goes inside {curly braces}."""
        self._tags[name] = resolver

    def unregister_tag(self, name: str) -> None:
        self._tags.pop(name, None)

    def has_tag(self, name: str) -> bool:
        return name in self._tags

    def resolve(self, text: str, player: Player) -> str:
        for name, resolver in self._tags.items():
            placeholder = "{" + name + "}"
            if placeholder not in text:
                continue
            try:
                text = text.replace(placeholder, resolver(player))
            except Exception:
                # A broken tag from some other plugin shouldn't break the board.
                text = text.replace(placeholder, "N/A")
        return text
