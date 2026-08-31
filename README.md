# Endstone Scoreboard

Per-player sidebar scoreboard for Endstone (Bedrock) servers, split into
small modules so other plugins can hook in their own placeholders without
touching this plugin's code.

Author: **Appolo**

## Install

1. From the project root, build the wheel:
   ```
   pip install hatch
   hatch build
   ```
2. Grab the `.whl` from `dist/` and drop it in your server's `plugins/` folder.
3. Start/restart the server.

For development, install straight from source instead:
```
pip install -e .
```

## Code layout

```
src/endstone_scoreboard/
├── __init__.py   -> exports ScoreboardPlugin & ScoreboardAPI
├── plugin.py     -> lifecycle, commands, events, tick loop
├── api.py        -> placeholder registry other plugins hook into
├── tags.py       -> built-in placeholders (also doubles as an example)
├── board.py      -> per-player rendering, only touches lines that changed
├── stats.py      -> JSON-backed kill/death counters
└── config.toml   -> default config
```

## Configuration

`config.toml` shows up under `plugins/endstone_scoreboard/config.toml`
after the plugin has run once. Available options:

- `enabled` - master on/off switch for the whole plugin
- `update-interval-ticks` - how often the board refreshes (20 ticks = ~1s)
- `show-on-join` - whether the board shows automatically on join
- `title` - board title, supports `&` color codes
- `lines` - board content, supports `&` color codes and placeholders

Built-in placeholders: `{player}`, `{online}`, `{max}`, `{ping}`,
`{level}`, `{tps}`, `{world_name}`, `{x}` `{y}` `{z}`, `{default_kills}`,
`{default_death}`.

Kills and deaths are tracked automatically (PvP kills only count towards
`{default_kills}`; any death counts towards `{default_death}`) and saved
to `plugins/endstone_scoreboard/stats.json`, so they survive restarts.

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
