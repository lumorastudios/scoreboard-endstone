# Endstone Scoreboard

Per-player sidebar scoreboard for Endstone (Bedrock) servers, split into
small modules so other plugins can hook in their own placeholders without
touching this plugin's code.

## Configuration

`config.toml` shows up under `plugins/endstone_scoreboard/config.toml`
after the plugin has run once. Available options:

- `enabled` - master on/off switch for the whole plugin
- `update-interval-ticks` - how often the board refreshes (20 ticks = ~1s)
- `show-on-join` - whether the board shows automatically on join
- `title` - board title, supports `&` color codes
- `lines` - board content, supports `&` color codes and placeholders

Placeholders: `{player}`, `{online}`, `{max}`, `{ping}`,
`{level}`, `{tps}`, `{world_name}`, `{x}` `{y}` `{z}`, `{default_kills}`,
`{default_death}`.

## Commands

- `/sb` - toggle your own board on/off (default: everyone can use it)
- `/sbreload` - reload config.toml without restarting (default: op only)

## For developers

Other plugins can register their own placeholders through this plugin's
API - no forking or editing required. From your own plugin:

```python
def on_enable(self) -> None:
    scoreboard = self.server.plugin_manager.get_plugin("scoreboard")
    if scoreboard is not None:
        scoreboard.api.register_tag("balance", lambda player: str(get_balance(player)))
```

Once registered, `{balance}` works in `config.toml`'s `lines` exactly like
the built-in placeholders (`{player}`, `{online}`, etc).

Since load order isn't guaranteed, always check `get_plugin(...)` isn't
None before using it, and declare `depend`/`soft_depend` on
`endstone-scoreboard` in your own plugin so it loads first.
