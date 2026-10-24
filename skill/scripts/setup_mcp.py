#!/usr/bin/env python3
"""本地配置 mcd-mcp；默认隐藏输入 Token，支持预览及指定配置路径。"""
import argparse
import getpass
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SERVER_KEY = "mcd-mcp"
DEFAULT_CONFIG_PATH = Path.home() / ".workbuddy" / "mcp.json"


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("现有配置不是合法 UTF-8 JSON；未修改文件，请先修复。") from exc
    if not isinstance(config, dict):
        raise ValueError("配置根节点必须是对象；未修改文件。")
    if "mcpServers" in config and not isinstance(config["mcpServers"], dict):
        raise ValueError("mcpServers 必须是对象；未修改文件。")
    entry = config.get("mcpServers", {}).get(SERVER_KEY, {})
    if not isinstance(entry, dict) or not isinstance(entry.get("headers", {}), dict):
        raise ValueError("现有 mcd-mcp 及 headers 必须是对象；未修改文件。")
    return config


def normalize_token(raw: str) -> str:
    token = raw.strip()
    if token.lower() == "bearer":
        token = ""
    elif token.lower().startswith("bearer "):
        token = token[6:].strip()
    if not token or any(char.isspace() for char in token):
        raise ValueError("Token 不能为空或包含空白。")
    if token in {"YOUR_MCP_TOKEN", "${MCD_MCP_TOKEN}"}:
        raise ValueError("请使用真实 Token，而非示例占位符。")
    return token


def configure(path: Path, token: str) -> bool:
    config = load_config(path)
    token = normalize_token(token)
    servers = config.setdefault("mcpServers", {})
    existing = servers.get(SERVER_KEY, {})
    if not isinstance(existing, dict):
        raise ValueError("现有 mcd-mcp 配置必须是对象；未修改文件。")
    # 保留连接器额外设置及其他请求头，仅更新必要字段。
    entry = dict(existing)
    headers = entry.get("headers", {})
    if not isinstance(headers, dict):
        raise ValueError("现有 headers 必须是对象；未修改文件。")
    headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
    headers["Authorization"] = f"Bearer {token}"
    entry.update(type="streamablehttp", url="https://mcp.mcd.cn", headers=headers)
    if servers.get(SERVER_KEY) == entry:
        return False
    servers[SERVER_KEY] = entry
    serialized = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    # 先完整写入临时文件，再备份及原子替换，避免中断造成半个 JSON。
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            stream.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        if path.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = path.with_name(f"{path.name}.bak.{stamp}")
            shutil.copyfile(path, backup)
            print(f"已备份原配置 -> {backup}")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH,
                        help="WorkBuddy MCP 配置路径，默认 ~/.workbuddy/mcp.json")
    parser.add_argument("--dry-run", action="store_true", help="只检查配置结构与目标路径，不读 Token、不写文件")
    args = parser.parse_args()
    path = args.config.expanduser().resolve()
    try:
        load_config(path)
        if args.dry_run:
            print(f"预览目标: {path}\n现有结构可合并；仅更新 mcd-mcp，写入前备份。未读 Token、未写文件。")
            return 0
        raw = os.environ.get("MCD_MCP_TOKEN")
        if raw is None:
            raw = getpass.getpass("请输入麦当劳 MCP Token（输入不回显）: ")
        changed = configure(path, raw)
        print(f"{'已配置' if changed else '配置已一致，无需修改'} -> {path}")
        print("配置及备份含凭证，请仅保留本地。下一步: WorkBuddy → 自定义连接器 → 启用 mcd-mcp。")
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print(f"配置失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
