#!/usr/bin/env python3
"""本地生成带标准留白的支付二维码 SVG；推荐用 --url-stdin 避免链接进入命令历史。"""
import argparse
import sys
from html import escape
from pathlib import Path
from urllib.parse import urlsplit


def validate_url(url: str) -> str:
    if not url or len(url) > 8192 or any(char.isspace() or ord(char) < 32 for char in url):
        raise ValueError("支付链接为空、过长或包含空白／控制字符。")
    try:
        parts = urlsplit(url)
        valid = parts.scheme == "https" and parts.hostname and not parts.username and not parts.password
        parts.port  # 同时验证端口格式。
    except ValueError as exc:
        raise ValueError("支付链接格式无效。") from exc
    if not valid:
        raise ValueError("仅接受无用户凭证的 HTTPS 绝对链接；链接必须来自本次官方订单响应。")
    return url


def build_svg(url: str, expires: str = "") -> str:
    validate_url(url)
    if len(expires) > 100 or any(ord(char) < 32 for char in expires):
        raise ValueError("截止时间文本过长或包含控制字符。")
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("缺少依赖，请执行 python -m pip install -r skill/requirements.txt") from exc
    qr = qrcode.QRCode(border=4, box_size=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    try:
        qr.make(fit=True)
    except (qrcode.exceptions.DataOverflowError, ValueError) as exc:
        raise ValueError("链接超过二维码容量，请直接打开本次订单原始支付链接。") from exc
    matrix = qr.get_matrix()
    modules = len(matrix)
    # 按模块数等比缩放；长支付链接不会超出固定卡片宽度。
    cell = max(1, min(10, 600 // modules))
    width = modules * cell
    x, y = (680 - width) // 2, 120
    height = y + width + 90
    path = "".join(f"M{col*cell},{row*cell}h{cell}v{cell}h-{cell}z"
                   for row, values in enumerate(matrix) for col, dark in enumerate(values) if dark)
    deadline = escape(f"支付截止：{expires}" if expires else "支付时效以当前订单返回信息为准")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 {height}" width="680" height="{height}" role="img">\n'
        '<title>当前订单支付二维码</title>\n'
        f'<rect width="680" height="{height}" fill="white"/>\n'
        '<text x="340" y="48" text-anchor="middle" font-family="sans-serif" font-size="22">扫码支付</text>\n'
        f'<text x="340" y="82" text-anchor="middle" font-family="sans-serif" font-size="14">{deadline}</text>\n'
        f'<g transform="translate({x},{y})"><path d="{path}" fill="black" shape-rendering="crispEdges"/></g>\n'
        f'<text x="340" y="{y+width+44}" text-anchor="middle" font-family="sans-serif" font-size="14">请核对官方收款页面、餐品和金额后支付</text>\n'
        '</svg>'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("url", nargs="?", help="支付链接；真实订单优先使用 --url-stdin")
    source.add_argument("--url-stdin", action="store_true", help="从标准输入读取支付链接")
    parser.add_argument("--expires", default="", help="订单实际返回的支付截止时间")
    parser.add_argument("--out", type=Path, help="输出 SVG；不指定则写到 stdout")
    args = parser.parse_args()
    try:
        url = sys.stdin.read().strip() if args.url_stdin else args.url
        svg = build_svg(url, args.expires)
        if args.out:
            args.out.write_text(svg, encoding="utf-8")
            print(f"已生成: {args.out}")
        else:
            print(svg)
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"二维码生成失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
