# ccswitch-sync

将 Claude Code 的插件配置、claude-hud 状态栏、工具搜索等设置同步到 CC Switch 的共享配置中，确保切换 provider 后配置不丢失。

## 解决的问题

CC Switch 在切换 provider 时可能覆盖 `~/.claude/settings.json`，导致：

- 已安装的插件没有启用，或 `/plugin list` 显示异常
- claude-hud 状态栏消失
- `ENABLE_TOOL_SEARCH`、`skipWebFetchPreflight` 等常用配置丢失

`ccswitch-sync` 会把这些配置写入 CC Switch 的 SQLite 共享配置 `settings.common_config_claude`，让它们在 provider 切换后继续保留。

## 功能

同步以下设置到 CC Switch 的 Claude 共享配置：

| 配置项 | 说明 |
| --- | --- |
| `enabledPlugins` | 从 `~/.claude/plugins/installed_plugins.json` 读取全部已安装插件并启用 |
| `statusLine` | 写入 claude-hud 状态栏命令，兼容 Windows + Git Bash / Cygwin |
| `env.ENABLE_TOOL_SEARCH` | 启用工具搜索，设为 `"true"` |
| `includeCoAuthoredBy` | 关闭 co-authored-by，设为 `false` |
| `skipWebFetchPreflight` | 跳过 WebFetch 预检，设为 `true` |

脚本仅读写 CC Switch 数据库里的 `common_config_claude` 字段，不读取或写入 API Key、provider endpoint 等敏感配置。

## 适用场景

适合在以下情况运行：

- CC Switch 覆盖了 `~/.claude/settings.json`
- 切换 provider 后插件没有启用
- 安装或卸载 Claude Code 插件后，需要刷新 CC Switch 共享配置
- claude-hud 直接运行正常，但通过 CC Switch 启动后不显示
- 希望 `ENABLE_TOOL_SEARCH`、`skipWebFetchPreflight` 等设置在 provider 切换后继续生效

## 安装

在 Claude Code 中添加并安装 marketplace：

```text
/plugin marketplace add <your-repo-url>
/plugin install ccswitch-sync
/reload-plugins
```

如果这是本地 skill，也可以把目录放到 Claude Code 可识别的 skills/plugin 路径后重新加载插件。

## 使用方法

在 Claude Code 中直接说：

```text
使用 ccswitch sync，把现在的插件配置同步到 ccswitch 中
```

Claude 会使用该 skill 并运行：

```bash
python scripts/sync_config.py
```

成功输出类似：

```text
[ccswitch-sync] Backed up DB → C:\Users\<you>\.cc-switch\backups\cc-switch-before-ccswitch-sync-20260525-171034.db
[ccswitch-sync] Found 17 installed plugins
[ccswitch-sync] Synced: 17 plugins, statusLine=YES, skipWebFetchPreflight=True
[ccswitch-sync] Done. Restart CC Switch or switch provider to apply.
```

完成后重启 CC Switch，或切换一次 provider并确保启用 `Write Shared Config`，即可应用配置。

## 工作原理

```text
~/.claude/plugins/installed_plugins.json
        │
        ▼
scripts/sync_config.py
        │
        ├─ 备份 ~/.cc-switch/cc-switch.db
        ├─ 读取已安装插件 ID
        ├─ 读取 settings.common_config_claude
        ├─ 合并 enabledPlugins / statusLine / env 等字段
        └─ 写回 CC Switch SQLite 数据库
```

脚本使用合并策略：

- 会更新本 skill 管理的字段
- 不会主动删除其他已有配置
- 每次写入前都会创建带时间戳的数据库备份

## 文件结构

```text
ccswitch-sync/
├── SKILL.md
├── README.md
└── scripts/
    └── sync_config.py
```

## 安全说明

- 写入前会备份 `~/.cc-switch/cc-switch.db` 到 `~/.cc-switch/backups/`
- 不处理 API Key、模型 endpoint、provider token 等敏感信息
- 如果 CC Switch 正在运行并锁定数据库，请先关闭 CC Switch 后重试
- 如果同步后配置未生效，请重启 CC Switch 或重新切换 provider

## 手动配置回退

如果脚本无法运行，可以手动把以下字段合并到 CC Switch 的 Claude shared config JSON：

```json
{
  "env": {
    "ENABLE_TOOL_SEARCH": "true"
  },
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

`enabledPlugins` 中的插件 ID 请以 `~/.claude/plugins/installed_plugins.json` 为准。

## 依赖

- Python 3.7+
- Claude Code
- CC Switch
- Windows + Git Bash / Cygwin 环境用于 claude-hud statusLine 命令

## License

MIT
