#!/usr/bin/env python3
"""离线验收：结构、公开材料、配置事务、二维码矩阵；不联网、不读取真实凭证。"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

QRCODE_AVAILABLE = importlib.util.find_spec("qrcode") is not None

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "skill" / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load_script("setup_mcp")
pay = load_script("pay_qr")


class OfflineChecks(unittest.TestCase):
    def test_required_files_and_metadata(self):
        for name in ("README.md", "CONTEST_DECLARATION.md", "MCP_INTEGRATION.md",
                     "mcp-config.example.json", "workbuddy.md", "SUBMISSION_CHECKLIST.md",
                     "skill/references/acceptance-cases.md"):
            self.assertTrue((ROOT / name).is_file(), name)
        content = (ROOT / "skill/SKILL.md").read_text(encoding="utf-8-sig")
        metadata = content.split("---", 2)[1]
        fields = dict(line.split(":", 1) for line in metadata.strip().splitlines())
        self.assertEqual(fields["name"].strip(), "mcnow")
        self.assertEqual(set(fields), {"name", "description"})
        self.assertTrue(1 <= len(fields["description"].strip()) <= 1024)
        example = json.loads((ROOT / "mcp-config.example.json").read_text(encoding="utf-8-sig"))
        server = example["mcpServers"]["mcd-mcp"]
        self.assertEqual(server["headers"]["Authorization"], "Bearer ${MCD_MCP_TOKEN}")
        self.assertEqual(server["url"], "https://mcp.mcd.cn")

    def test_local_document_links(self):
        for doc in ROOT.rglob("*.md"):
            if any(part in {".git", "dist"} for part in doc.relative_to(ROOT).parts):
                continue
            content = doc.read_text(encoding="utf-8-sig")
            links = re.findall(r'\]\(([^)\s]+)\)|(?:src|href)="([^"]+)"', content)
            for pair in links:
                link = next(item for item in pair if item).split("#", 1)[0]
                if not link or re.match(r"[a-zA-Z][\w+.-]*:", link):
                    continue
                self.assertTrue((doc.parent / link).exists(), f"{doc.relative_to(ROOT)}: {link}")

    def test_public_files_no_obvious_credentials(self):
        # 只覆盖本项目公开文本；不读取工作目录之外的配置，不输出匹配到的值。
        patterns = (r"(?i)Bearer\s+(?!\$\{)[A-Za-z0-9_.-]{24,}",
                    r"gh[pousr]_[A-Za-z0-9]{30,}", r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----")
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(part in {".git", "dist", "__pycache__"} for part in path.relative_to(ROOT).parts):
                continue
            if path.suffix not in {".md", ".py", ".json", ".txt", ".yml", ".yaml"}:
                continue
            content = path.read_text(encoding="utf-8-sig")
            for pattern in patterns:
                self.assertIsNone(re.search(pattern, content), f"疑似凭证: {path.relative_to(ROOT)}")

    def test_config_preservation_backup_and_idempotence(self):
        with tempfile.TemporaryDirectory(prefix="mcnow-test-") as folder:
            target = Path(folder) / "mcp.json"
            original = {"theme": "dark", "mcpServers": {"other": {"url": "https://example.com"},
                        "mcd-mcp": {"disabled": True, "headers": {"X-Extra": "keep"}}}}
            target.write_text(json.dumps(original), encoding="utf-8")
            before = target.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(setup.configure(target, "Bearer fixture-only"))
                self.assertFalse(setup.configure(target, "fixture-only"))
            result = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(result["theme"], "dark")
            self.assertEqual(result["mcpServers"]["other"], original["mcpServers"]["other"])
            self.assertTrue(result["mcpServers"]["mcd-mcp"]["disabled"])
            self.assertEqual(result["mcpServers"]["mcd-mcp"]["headers"]["X-Extra"], "keep")
            backups = list(Path(folder).glob("*.bak.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), before)

    def test_config_rejects_invalid_input_without_writes(self):
        with tempfile.TemporaryDirectory(prefix="mcnow-test-") as folder:
            target = Path(folder) / "mcp.json"
            for content in ("{broken", "[]", '{"mcpServers": []}', '{"mcpServers":{"mcd-mcp":[]}}',
                            '{"mcpServers":{"mcd-mcp":{"headers":[]}}}'):
                target.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    setup.configure(target, "fixture-only")
                self.assertEqual(target.read_text(encoding="utf-8"), content)
            for token in ("", "Bearer ", "bad token", "${MCD_MCP_TOKEN}"):
                with self.assertRaises(ValueError):
                    setup.normalize_token(token)

    def test_config_atomic_replace_failure_keeps_original(self):
        with tempfile.TemporaryDirectory(prefix="mcnow-test-") as folder:
            target = Path(folder) / "mcp.json"
            target.write_text("{}", encoding="utf-8")
            with patch.object(setup.os, "replace", side_effect=OSError("模拟替换失败")):
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(OSError):
                    setup.configure(target, "fixture-only")
            self.assertEqual(target.read_text(encoding="utf-8"), "{}")
            self.assertFalse(list(Path(folder).glob(".mcp.json.*")))

    def test_config_dry_run_does_not_prompt_or_create(self):
        with tempfile.TemporaryDirectory(prefix="mcnow-test-") as folder:
            target = Path(folder) / "nested" / "mcp.json"
            with patch.object(sys, "argv", ["setup_mcp.py", "--config", str(target), "--dry-run"]), \
                 patch.object(setup.getpass, "getpass", side_effect=AssertionError("不应读取 Token")), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(setup.main(), 0)
            self.assertFalse(target.parent.exists())

    def test_qr_url_validation(self):
        for url in ("", "http://example.com", "javascript:alert(1)", "https://user:pass@example.com",
                    "https://example.com/with space", "https://", "https://example.com:bad"):
            with self.assertRaises(ValueError):
                pay.build_svg(url)

    @unittest.skipUnless(QRCODE_AVAILABLE, "未安装 qrcode；先执行 python -m pip install -r skill/requirements.txt")
    def test_qr_matrix_quiet_zone_and_bounds(self):
        import qrcode
        ns = {"s": "http://www.w3.org/2000/svg"}
        # 短链及接近最大容量的合成长链，验证输出编码的每个深色模块及边界。
        for url in ("https://example.com/pay?order=fixture", "https://example.com/pay?data=" + "a" * 1800):
            root = ET.fromstring(pay.build_svg(url, '2026-10-25 12:00 <截止>'))
            group = root.find("s:g", ns)
            path = group.find("s:path", ns).attrib["d"]
            cells = re.findall(r"M(\d+),(\d+)h(\d+)v(\d+)h-(\d+)z", path)
            qr = qrcode.QRCode(border=4, box_size=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(url)
            qr.make(fit=True)
            matrix = qr.get_matrix()
            cell = int(cells[0][2])
            actual = {(int(x) // cell, int(y) // cell) for x, y, *_ in cells}
            expected = {(col, row) for row, values in enumerate(matrix) for col, dark in enumerate(values) if dark}
            self.assertEqual(actual, expected)
            self.assertTrue(all(4 <= x < len(matrix)-4 and 4 <= y < len(matrix)-4 for x, y in actual))
            x, y = map(int, re.findall(r"\d+", group.attrib["transform"]))
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x + len(matrix)*cell, 680)
            self.assertLessEqual(y + len(matrix)*cell, int(root.attrib["height"]))
            self.assertNotIn(url, ET.tostring(root, encoding="unicode"))

    @unittest.skipUnless(QRCODE_AVAILABLE, "未安装 qrcode；先执行 python -m pip install -r skill/requirements.txt")
    def test_qr_stdin_cli(self):
        with tempfile.TemporaryDirectory(prefix="mcnow-test-") as folder:
            target = Path(folder) / "pay.svg"
            with patch.object(sys, "argv", ["pay_qr.py", "--url-stdin", "--out", str(target)]), \
                 patch.object(sys, "stdin", io.StringIO("https://example.com/fixture\n")), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(pay.main(), 0)
            ET.parse(target)

    @unittest.skipUnless(QRCODE_AVAILABLE, "未安装 qrcode")
    def test_qr_capacity_overflow_is_actionable(self):
        with self.assertRaisesRegex(ValueError, "二维码容量"):
            pay.build_svg("https://example.com/pay?data=" + "a" * 6000)


def package_skill():
    destination = ROOT / "dist" / "mcnow-skill.zip"
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "skill").rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, Path("mcnow") / path.relative_to(ROOT / "skill"))
    print(f"已打包: {destination}")
    print(f"SHA256: {hashlib.sha256(destination.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true", help="验收通过后将 Skill 打包到 dist/mcnow-skill.zip")
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OfflineChecks))
    complete = result.wasSuccessful() and not result.skipped
    if args.package and not complete:
        print("打包失败：必须安装依赖并完成全部测试，不允许跳过。", file=sys.stderr)
    if args.package and complete:
        package_skill()
    sys.exit(0 if result.wasSuccessful() and (not args.package or complete) else 1)
