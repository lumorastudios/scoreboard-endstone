# One player's live scoreboard.
#
# Two things here matter more than they look:
#
# 1. The player is assigned to the scoreboard *before* we flip the display
#    slot on. Do it the other way round and the "show sidebar" packet has
#    nobody to reach yet, so the board never actually appears on screen.
# 2. render() remembers what it drew last time and only touches the lines
#    that changed, instead of wiping and re-adding everything every tick -
#    that's what avoids the board flickering on Bedrock clients.

from typing import List

from endstone import Player
from endstone.scoreboard import Criteria, DisplaySlot, ObjectiveSortOrder, RenderType

from endstone_scoreboard.api import ScoreboardAPI

OBJECTIVE_NAME = "sidebar"
COLOR_CHAR = "\u00a7"


def colorize(text: str) -> str:
    return text.replace("&", COLOR_CHAR)


class Board:
    def __init__(self, server, player: Player, title: str) -> None:
        self.player = player
        self._lines: List[str] = []

        self.scoreboard = server.create_scoreboard()
        self.objective = self.scoreboard.add_objective(
            OBJECTIVE_NAME, Criteria.Type.DUMMY, colorize(title), RenderType.INTEGER
        )
        player.scoreboard = self.scoreboard
        self.objective.set_display(DisplaySlot.SIDE_BAR, ObjectiveSortOrder.DESCENDING)

    def render(self, raw_lines: List[str], api: ScoreboardAPI) -> None:
        new_lines = [colorize(api.resolve(line, self.player)) for line in raw_lines]

        # Duplicate lines (two blanks, say) would collapse into one entry,
        # so each gets padded with a unique, invisible number of resets.
        new_entries = [text + (COLOR_CHAR + "r") * i for i, text in enumerate(new_lines)]
        old_entries = [text + (COLOR_CHAR + "r") * i for i, text in enumerate(self._lines)]

        total = len(new_entries)

        for index, entry in enumerate(new_entries):
            if index < len(old_entries) and old_entries[index] == entry:
                continue  # nothing changed on this line, leave it alone
            if index < len(old_entries):
                self.scoreboard.reset_scores(old_entries[index])
            self.objective.get_score(entry).value = total - index

        # Lines that used to exist but the config no longer has.
        for entry in old_entries[total:]:
            self.scoreboard.reset_scores(entry)

        self._lines = new_lines
