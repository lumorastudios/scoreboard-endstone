# Scoreboard plugin for Endstone.
# Gives every player their own sidebar scoreboard, fully driven by config.toml.
# Author: Appolo

from endstone import Player
from endstone.command import Command, CommandSender
from endstone.event import PlayerJoinEvent, PlayerQuitEvent, event_handler
from endstone.plugin import Plugin
from endstone.scoreboard import (
    Criteria,
    DisplaySlot,
    Objective,
    ObjectiveSortOrder,
    RenderType,
    Scoreboard,
)

# Name of the objective we register on each player's scoreboard.
# This is internal only, players never see it.
OBJECTIVE_NAME = "sidebar"

# The actual character Minecraft uses for color/formatting codes.
COLOR_CHAR = "\u00a7"


class ScoreboardPlugin(Plugin):
    api_version = "0.11"
    description = "Configurable sidebar scoreboard for every player."
    authors = ["Appolo"]
    prefix = "Scoreboard"

    commands = {
        "sb": {
            "description": "Toggle your sidebar scoreboard on or off.",
            "usages": ["/sb"],
            "permissions": ["scoreboard.command.sb"],
        },
        "sbreload": {
            "description": "Reload the scoreboard config.toml.",
            "usages": ["/sbreload"],
            "permissions": ["scoreboard.command.sbreload"],
        },
    }

    permissions = {
        "scoreboard.command.sb": {
            "description": "Lets a player toggle their own scoreboard.",
            "default": True,
        },
        "scoreboard.command.sbreload": {
            "description": "Lets a player reload the scoreboard config.",
            "default": "op",
        },
    }

    def on_load(self) -> None:
        self.logger.info("Scoreboard loading...")

    def on_enable(self) -> None:
        self.save_default_config()
        self._load_settings()

        # Tracks which players currently have the board visible, keyed by
        # their UUID so it survives a name change during the session.
        self._visible = {}

        self.register_events(self)
        self.server.scheduler.run_task(self, self._tick, delay=0, period=self._interval)

        # In case the plugin got reloaded while people were already online.
        for player in self.server.online_players:
            self._visible[player.unique_id] = self._show_on_join
            if self._enabled and self._show_on_join:
                self._attach_board(player)

        self.logger.info("Scoreboard enabled.")

    def on_disable(self) -> None:
        self.server.scheduler.cancel_tasks(self)
        self.logger.info("Scoreboard disabled.")

    # ------------------------------------------------------------------
    # config.toml
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        config = self.config
        self._enabled = config.get("enabled", True)
        self._interval = max(1, config.get("update-interval-ticks", 20))
        self._show_on_join = config.get("show-on-join", True)
        self._title = self._colorize(config.get("title", "&e&lSERVER"))
        self._lines = config.get("lines", [])

    # ------------------------------------------------------------------
    # commands
    # ------------------------------------------------------------------

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name == "sb":
            if not isinstance(sender, Player):
                sender.send_message("This command can only be used in-game.")
                return True
            self._toggle(sender)
            return True

        if command.name == "sbreload":
            self.reload_config()
            self._load_settings()
            sender.send_message(f"{COLOR_CHAR}aScoreboard config reloaded.")
            return True

        return False

    def _toggle(self, player: Player) -> None:
        if not self._enabled:
            player.send_message(f"{COLOR_CHAR}cScoreboard is disabled on this server.")
            return

        visible = not self._visible.get(player.unique_id, self._show_on_join)
        self._visible[player.unique_id] = visible

        if visible:
            self._attach_board(player)
            player.send_message(f"{COLOR_CHAR}aScoreboard turned on.")
        else:
            player.scoreboard = self.server.create_scoreboard()
            player.send_message(f"{COLOR_CHAR}cScoreboard turned off.")

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        player = event.player
        self._visible[player.unique_id] = self._show_on_join
        if self._enabled and self._show_on_join:
            self._attach_board(player)

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent) -> None:
        self._visible.pop(event.player.unique_id, None)

    # ------------------------------------------------------------------
    # board building
    # ------------------------------------------------------------------

    def _attach_board(self, player: Player) -> None:
        board = self.server.create_scoreboard()
        objective = board.add_objective(
            OBJECTIVE_NAME, Criteria.Type.DUMMY, self._title, RenderType.INTEGER
        )
        objective.set_display(DisplaySlot.SIDE_BAR, ObjectiveSortOrder.DESCENDING)
        player.scoreboard = board

    def _tick(self) -> None:
        if not self._enabled:
            return

        for player in self.server.online_players:
            if not self._visible.get(player.unique_id, self._show_on_join):
                continue

            try:
                board = player.scoreboard
                objective = board.get_objective(OBJECTIVE_NAME) if board else None
                if objective is None:
                    self._attach_board(player)
                    continue
                self._render(player, board, objective)
            except Exception as error:
                # One broken board should never take the rest down with it.
                self.logger.warning(f"Could not update board for {player.name}: {error}")

    def _render(self, player: Player, board: Scoreboard, objective: Objective) -> None:
        # Placeholders like {online} change over time, so the entry text
        # changes too - wipe everything first or old lines pile up forever.
        for entry in list(board.entries):
            board.reset_scores(entry)

        total = len(self._lines)
        for index, raw_line in enumerate(self._lines):
            text = self._colorize(self._apply_placeholders(raw_line, player))

            # Two identical lines would collapse into the same scoreboard
            # entry, so pad each with a unique, invisible amount of resets.
            entry = text + (COLOR_CHAR + "r") * index

            score = objective.get_score(entry)
            score.value = total - index

    def _apply_placeholders(self, text: str, player: Player) -> str:
        return (
            text.replace("{player}", player.name)
            .replace("{online}", str(len(self.server.online_players)))
            .replace("{max}", str(self.server.max_players))
            .replace("{ping}", str(player.ping))
            .replace("{level}", str(player.exp_level))
            .replace("{tps}", f"{self.server.current_tps:.1f}")
        )

    @staticmethod
    def _colorize(text: str) -> str:
        return text.replace("&", COLOR_CHAR)
