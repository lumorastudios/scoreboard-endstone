# Built-in tags. Nothing about these is special - they're registered
# through the exact same register_tag() call an external plugin would use.
# Treat this file as an example of how to add your own.

import time

from endstone import Server
from endstone.actor import Actor

from endstone_scoreboard.api import ScoreboardAPI
from endstone_scoreboard.stats import StatsStore


def _dimension_name(actor: Actor) -> str:
    # Newer Endstone builds expose Dimension.id (e.g. "minecraft:the_nether")
    # instead of the old Dimension.name, so try both and keep the short part.
    dimension = actor.dimension
    identifier = getattr(dimension, "id", None) or getattr(dimension, "name", "world")
    return str(identifier).split(":")[-1]


def _ec_balance(player, server: Server) -> str:
    # If EndstoneCore isn't installed this raises, and the API layer already
    # catches that and shows "N/A" - no need to duplicate that check here.
    core = server.plugin_manager.get_plugin("core")
    return core.manager.money(core.manager.get_balance(player))


def _ec_playtime(player, server: Server) -> str:
    core = server.plugin_manager.get_plugin("core")
    record = core.manager.player_record(player)
    seconds = int(record.get("playtime_seconds", 0))
    seconds += max(0, int(time.time()) - int(record.get("session_started", int(time.time()))))
    return core.manager.duration_text(seconds)


def register_defaults(api: ScoreboardAPI, server: Server, stats: StatsStore) -> None:
    api.register_tag("player", lambda p: p.name)
    api.register_tag("online", lambda p: str(len(server.online_players)))
    api.register_tag("max", lambda p: str(server.max_players))
    api.register_tag("ping", lambda p: str(p.ping))
    api.register_tag("level", lambda p: str(p.exp_level))
    api.register_tag("tps", lambda p: f"{server.current_tps:.1f}")

    api.register_tag("world_name", _dimension_name)
    api.register_tag("x", lambda p: str(int(p.location.x)))
    api.register_tag("y", lambda p: str(int(p.location.y)))
    api.register_tag("z", lambda p: str(int(p.location.z)))

    api.register_tag("default_kills", lambda p: str(stats.kills(str(p.unique_id))))
    api.register_tag("default_death", lambda p: str(stats.deaths(str(p.unique_id))))

    # These two need the EndstoneCore plugin (entry point name "core")
    # installed alongside this one - they show "N/A" otherwise.
    api.register_tag("ec_balance", lambda p: _ec_balance(p, server))
    api.register_tag("ec_playtime", lambda p: _ec_playtime(p, server))
