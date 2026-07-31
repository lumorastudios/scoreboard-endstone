# Built-in tags. Nothing about these is special - they're registered
# through the exact same register_tag() call an external plugin would use.
# Treat this file as an example of how to add your own.

from endstone import Server

from endstone_scoreboard.api import ScoreboardAPI


def register_defaults(api: ScoreboardAPI, server: Server) -> None:
    api.register_tag("player", lambda p: p.name)
    api.register_tag("online", lambda p: str(len(server.online_players)))
    api.register_tag("max", lambda p: str(server.max_players))
    api.register_tag("ping", lambda p: str(p.ping))
    api.register_tag("level", lambda p: str(p.exp_level))
    api.register_tag("tps", lambda p: f"{server.current_tps:.1f}")
