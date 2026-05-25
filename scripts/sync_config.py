"""
Sync Claude Code plugin & HUD config into CC Switch shared config (common_config_claude).

Reads installed plugins from ~/.claude/plugins/installed_plugins.json, reads the current
common_config_claude from CC Switch's SQLite DB, merges enabledPlugins + statusLine +
skipWebFetchPreflight, backs up the DB, and writes the merged config back.

Safe to run repeatedly — it merges, never removes existing keys.
"""
import json
import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
CCSWITCH_DIR = HOME / ".cc-switch"

INSTALLED_PLUGINS = CLAUDE_DIR / "plugins" / "installed_plugins.json"
CCSWITCH_DB = CCSWITCH_DIR / "cc-switch.db"
BACKUPS_DIR = CCSWITCH_DIR / "backups"

# ── statusLine command (Windows + Git Bash / Cygwin compatible) ──────────
STATUSLINE_COMMAND = (
    "cols=$(stty size </dev/tty 2>/dev/null | awk '{print $2}'); "
    "export COLUMNS=$(( ${cols:-120} > 4 ? ${cols:-120} - 4 : 1 )); "
    "plugin_dir=$(ls -1d \"${CLAUDE_CONFIG_DIR:-$HOME/.claude}\"/plugins/cache/*/claude-hud/*/ 2>/dev/null | sort -V | tail -1); "
    "exec \"/c/Program Files/nodejs/node\" \"${plugin_dir}dist/index.js\""
)


def back_up_db() -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = BACKUPS_DIR / f"cc-switch-before-ccswitch-sync-{ts}.db"
    shutil.copy2(CCSWITCH_DB, dst)
    return dst


def load_installed_plugins() -> dict[str, bool]:
    if not INSTALLED_PLUGINS.exists():
        print(f"[ccswitch-sync] WARNING: {INSTALLED_PLUGINS} not found — no plugins to sync")
        return {}
    with INSTALLED_PLUGINS.open("r", encoding="utf-8") as f:
        plugin_ids = sorted(json.load(f)["plugins"].keys())
    return {pid: True for pid in plugin_ids}


def main():
    if not CCSWITCH_DB.exists():
        print(f"[ccswitch-sync] ERROR: CC Switch database not found at {CCSWITCH_DB}")
        print("[ccswitch-sync] Is CC Switch installed? Skipping sync.")
        sys.exit(1)

    backup_path = back_up_db()
    print(f"[ccswitch-sync] Backed up DB → {backup_path}")

    plugins = load_installed_plugins()
    print(f"[ccswitch-sync] Found {len(plugins)} installed plugins")

    with sqlite3.connect(CCSWITCH_DB) as con:
        cur = con.cursor()
        row = cur.execute(
            "SELECT value FROM settings WHERE key = ?",
            ("common_config_claude",),
        ).fetchone()
        config = json.loads(row[0]) if row and row[0].strip() else {}

        # Merge (never remove existing keys)
        config.setdefault("env", {})["ENABLE_TOOL_SEARCH"] = "true"
        config["includeCoAuthoredBy"] = False
        config["skipWebFetchPreflight"] = True
        if plugins:
            config["enabledPlugins"] = plugins
        config["statusLine"] = {
            "type": "command",
            "command": STATUSLINE_COMMAND,
        }

        output = json.dumps(config, ensure_ascii=False, indent=2)
        cur.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("common_config_claude", output),
        )
        con.commit()

    # Verify
    with sqlite3.connect(CCSWITCH_DB) as con:
        cfg = json.loads(
            con.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("common_config_claude",),
            ).fetchone()[0]
        )
    print(f"[ccswitch-sync] Synced: {len(cfg.get('enabledPlugins', {}))} plugins, "
          f"statusLine={'YES' if cfg.get('statusLine', {}).get('command') else 'NO'}, "
          f"skipWebFetchPreflight={cfg.get('skipWebFetchPreflight')}")
    print("[ccswitch-sync] Done. Restart CC Switch or switch provider to apply.")


if __name__ == "__main__":
    main()
