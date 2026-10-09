#!/usr/bin/env python3
"""生成麦当劳支付二维码（内联 SVG，可直接嵌入对话卡片）。

用法:
    python pay_qr.py <pay_url> [--out <输出路径.svg>]

- 不传 --out 时打印 SVG 到 stdout
- 依赖: qrcode (pip install qrcode)
- 输出为单 <path> 紧凑 SVG，必须内联渲染，禁止用 <img src="本地路径"> 引用
  （实测本地路径引用在对话预览中会裂图）
"""
import argparse
import sys

try:
    import qrcode
except ImportError:
    sys.exit("缺少依赖: 请先 pip install qrcode")


def build_svg(url: str) -> str:
    qr = qrcode.QRCode(border=0, box_size=1)
    qr.add_data(url)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    cs = 10
    w = n * cs
    oy = 140
    total_h = oy + w + 110
    ox = (680 - w) // 2
    d = "".join(
        f"M{c*cs},{r*cs}h{cs}v{cs}h-{cs}z"
        for r, row in enumerate(m)
        for c, v in enumerate(row)
        if v
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 {total_h}" width="100%">\n'
        f'<rect width="680" height="{total_h}" fill="#ffffff"/>\n'
        '<text x="340" y="56" text-anchor="middle" font-family="sans-serif" '
        'font-size="15" font-weight="500" fill="#1a1a1a">扫码支付</text>\n'
        '<text x="340" y="86" text-anchor="middle" font-family="sans-serif" '
        'font-size="13" fill="#8a8a8a">请在订单时效内完成支付 · 超时订单作废</text>\n'
        f'<rect x="{ox-24}" y="{oy-24}" width="{w+48}" height="{w+48}" rx="12" '
        'fill="#ffffff" stroke="#d3d1c7" stroke-width="0.5"/>\n'
        f'<g transform="translate({ox},{oy})"><path d="{d}" fill="#1a1a1a"/></g>\n'
        f'<text x="340" y="{oy+w+64}" text-anchor="middle" font-family="sans-serif" '
        'font-size="12" fill="#8a8a8a">微信/浏览器扫码，或打开麦当劳 App 支付</text>\n'
        '</svg>'
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="生成麦当劳支付二维码 SVG")
    ap.add_argument("url", help="支付链接（create-order 返回的 payH5Url）")
    ap.add_argument("--out", help="输出文件路径（缺省打印到 stdout）")
    args = ap.parse_args()
    svg = build_svg(args.url)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"saved: {args.out}")
    else:
        print(svg)


if __name__ == "__main__":
    main()
