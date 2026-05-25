---
name: ccswitch-sync
description: Sync Claude Code plugin activation, claude-hud statusLine, tool-search env, and WebFetch preflight settings into CC Switch's Claude shared config. Use this whenever CC Switch overwrites ~/.claude/settings.json, plugins disappear after provider switching, /plugin list is empty, claude-hud stops showing after CC Switch starts, or the user asks to persist Claude Code plugin/HUD settings through CC Switch shared/common config.
---

# CC Switch Claude Shared Config Sync

Use this skill to persist Claude Code plugin and HUD settings through CC Switch. CC Switch can overwrite `~/.claude/settings.json` when switching providers; the stable place for common Claude settings is its SQLite `settings.common_config_claude` value.

## What this skill does

Run the bundled script to merge these settings into CC Switch's Claude shared config:

- `enabledPlugins`: all currently installed Claude Code plugins from `~/.claude/plugins/installed_plugins.json`
- `statusLine`: claude-hud command for Windows + Git Bash/Cygwin
- `env.ENABLE_TOOL_SEARCH = "true"`
- `includeCoAuthoredBy = false`
- `skipWebFetchPreflight = true`

The script backs up `~/.cc-switch/cc-switch.db` before writing and only updates `settings.common_config_claude`; it does not read or write API keys or provider endpoints.

## When to run

Run this when:

- CC Switch overwrote `~/.claude/settings.json`
- `/plugin list` is empty after switching providers
- installed plugins exist in `installed_plugins.json` but are not enabled
- claude-hud works directly but does not appear after launching through CC Switch
- the user adds/removes plugins and wants CC Switch shared config refreshed
- the user wants `skipWebFetchPreflight` or other common Claude settings to survive provider switches

## Procedure

1. Confirm CC Switch exists at `~/.cc-switch/cc-switch.db`.
2. Confirm installed plugins exist at `~/.claude/plugins/installed_plugins.json`.
3. Run:

```bash
python scripts/sync_config.py
```

4. Read the script output. A successful run prints:

```text
[ccswitch-sync] Backed up DB → ...
[ccswitch-sync] Found N installed plugins
[ccswitch-sync] Synced: N plugins, statusLine=YES, skipWebFetchPreflight=True
[ccswitch-sync] Done. Restart CC Switch or switch provider to apply.
```

5. Tell the user to restart CC Switch or switch provider with "Write Shared Config" enabled.

## Safety notes

- Do not paste API keys or endpoint values into the report.
- The script creates a timestamped backup under `~/.cc-switch/backups/` before modifying the database.
- If the script fails, report the error and the backup path if one was created.
- If CC Switch is running and locks the database, ask the user to close CC Switch and rerun.

## Manual fallback

If the script cannot run, manually add these fields to CC Switch's Claude shared config JSON:

```json
{
  "env": { "ENABLE_TOOL_SEARCH": "true" },
  "includeCoAuthoredBy": false,
  "skipWebFetchPreflight": true,
  "enabledPlugins": {
    "plugin-id@marketplace": true
  },
  "statusLine": {
    "type": "command",
    "command": "cols=$(stty size </dev/tty 2>/dev/null | awk '{print $2}'); export COLUMNS=$(( ${cols:-120} > 4 ? ${cols:-120} - 4 : 1 )); plugin_dir=$(ls -1d \"${CLAUDE_CONFIG_DIR:-$HOME/.claude}\"/plugins/cache/*/claude-hud/*/ 2>/dev/null | sort -V | tail -1); exec \"/c/Program Files/nodejs/node\" \"${plugin_dir}dist/index.js\""
  }
}
```

Use the actual plugin IDs from `~/.claude/plugins/installed_plugins.json`.
