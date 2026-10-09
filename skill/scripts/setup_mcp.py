#!/usr/bin/env python3
"""一键配置麦当劳 mcd-mcp 连接器（写入 WorkBuddy MCP 配置）。

用法:
    python setup_mcp.py <你的MCP_TOKEN>
    python setup_mcp.py              # 未传参则安全提示输入（隐藏回显）

行为:
- 配置文件: ~/.workbuddy/mcp.json
- 只合并/更新 mcd-mcp 这一项，不动其他已有连接器配置
- 幂等：重复运行安全；修改前自动备份为 mcp.json.bak
- Token 只写入本地配置文件，不做任何网络请求

完成后请打开 WorkBuddy → 连接器 → 自定义连接器，启用（Trust）mcd-mcp。
MCP Token 申请: https://github.com/M-China/mcd-mcp-server
"""
import json
import sys
import time
from pathlib import Path

CONFIG_PATH = Path.home() / ".workbuddy" / "mcp.json"
SERVER_KEY = "mcd-mcp"
SERVER_CONFIG = {
    "type": "streamablehttp",
    "url": "https://mcp.mcd.cn",
    "headers": {},
}


def get_token() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1].strip()
    import getpass
    try:
        return getpass.getpass("请输入麦当劳 MCP Token（输入不回显）: ").strip()
    except EOFError:
        return ""


def main() -> None:
    token = get_token()
    if not token:
        sys.exit("错误: Token 不能为空。用法: python setup_mcp.py <MCP_TOKEN>")
    if token.upper().startswith("Bearer "):
        token = token[7:].strip()

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if CONFIG_PATH.exists():
        backup = CONFIG_PATH.with_suffix(f".json.bak.{int(time.time())}")
        backup.write_text(CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"已备份原配置 -> {backup}")
        try:
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sys.exit(f"错误: {CONFIG_PATH} 不是合法 JSON，请先修复或手动备份后删除重试")

    servers = config.setdefault("mcpServers", {})
    action = "更新" if SERVER_KEY in servers else "添加"
    entry = dict(SERVER_CONFIG)
    entry["headers"] = {"Authorization": f"Bearer {token}"}
    servers[SERVER_KEY] = entry

    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已{action} {SERVER_KEY} -> {CONFIG_PATH}")
    print("下一步: 打开 WorkBuddy → 连接器 → 自定义连接器，启用（Trust）mcd-mcp 即可使用。")


if __name__ == "__main__":
    main()
