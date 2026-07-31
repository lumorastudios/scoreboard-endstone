# Scoreboard plugin for Endstone.
#
# Structured so other plugins can plug their own placeholders in instead of
# forking this code - see api.py for the part that matters to them.
#
# Author: Appolo

from typing import Dict

from endstone import Player
from endstone.command import Command, CommandSender
from endstone.event import PlayerJoinEvent, PlayerQuitEvent, event_handler
from endstone.plugin import Plugin

from endstone_scoreboard.api import ScoreboardAPI
from endstone_scoreboard.board import Board
from endstone_scoreboard.tags import register_defaults

COLOR_CHAR = "\u00a7"


class ScoreboardPlugin(Plugin):
    api_version = "0.11"
    description = "Configurable sidebar scoreboard with a tag API for other plugins."
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
        # Public entry point for other plugins:
        #   self.server.plugin_manager.get_plugin("scoreboard").api.register_tag(...)
        self.api = ScoreboardAPI()

    def on_enable(self) -> None:
        self.save_default_config()
        self._load_settings()
        register_defaults(self.api, self.server)

        self._boards: Dict = {}  # player.unique_id -> Board
        self._visible: Dict = {}  # player.unique_id -> bool

        self.register_events(self)
        self.server.scheduler.run_task(self, self._tick, delay=0, period=self._interval)
        self._refresh_all()

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
        self._title = config.get("title", "&e&lSERVER")
        self._lines = config.get("lines", [])
        self.logger.info(
            f"Config loaded: enabled={self._enabled}, show_on_join={self._show_on_join}, "
            f"title={self._title!r}, lines={len(self._lines)}"
        )

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
            self._refresh_all()
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
            self._boards.pop(player.unique_id, None)
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
        self._boards.pop(event.player.unique_id, None)

    # ------------------------------------------------------------------
    # refresh loop
    # ------------------------------------------------------------------

    def _attach_board(self, player: Player) -> None:
        # Bedrock hides a sidebar slot entirely until it has at least one
        # score set, so render right away instead of waiting for the next
        # scheduled tick - otherwise the board can sit invisible for a
        # second or more after join/toggle.
        board = Board(self.server, player, self._title)
        self._boards[player.unique_id] = board
        try:
            board.render(self._lines, self.api)
            self.logger.info(f"Board attached for {player.name} ({len(self._lines)} lines).")
        except Exception as error:
            self.logger.warning(f"Could not render initial board for {player.name}: {error}")

    def _refresh_all(self) -> None:
        # Re-creates every visible player's board. Used on enable/reload so
        # a changed title or line count shows up immediately.
        for player in self.server.online_players:
            visible = self._visible.get(player.unique_id, self._show_on_join)
            self._visible[player.unique_id] = visible
            if self._enabled and visible:
                self._attach_board(player)
            else:
                self._boards.pop(player.unique_id, None)

    def _tick(self) -> None:
        if not self._enabled:
            return

        for player in self.server.online_players:
            board = self._boards.get(player.unique_id)
            if board is None:
                continue

            try:
                board.render(self._lines, self.api)
            except Exception as error:
                # One broken board should never take the rest down with it.
                self.logger.warning(f"Could not update board for {player.name}: {error}")
