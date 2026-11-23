#!/usr/bin/env python3
"""イベントの文字だけのアイキャッチ（無料。外の API を呼ばない）。spec 004。

使い方
  python3 make_eyecatch.py --title "<題>" --date 2026-12-11 [--sub "<場所など>"] [--label EVENT]
                           [--size 1080x1080] [--bg "#113a24"] [--fg "#f0f0f0"] [--accent "#38c37b"]
                           [--font <日本語が出るフォントのパス>] --out eyecatch.png
大きさの初期値は正方形（1080x1080）。告知サービスに合う大きさは使う側で --size か config で変える。
Pillow が要る（scripts/requirements.txt）。
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.stderr.write("Pillow が要ります：pip install -r scripts/requirements.txt\n")
    sys.exit(2)

DEFAULT_FONTS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(path, size):
    for p in [path, *DEFAULT_FONTS]:
        if p and Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def wrap(draw, text, f, width):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=f) > width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    return lines + ([cur] if cur else [])


def main():
    p = argparse.ArgumentParser(description="文字だけのアイキャッチ")
    p.add_argument("--title", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--sub", default="")
    p.add_argument("--label", default="EVENT")
    p.add_argument("--size", default="1080x1080")
    p.add_argument("--bg", default="#113a24")
    p.add_argument("--fg", default="#f0f0f0")
    p.add_argument("--accent", default="#38c37b")
    p.add_argument("--font")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    try:
        w, h = (int(x) for x in a.size.lower().split("x"))
    except ValueError:
        sys.stderr.write("--size は 1080x1080 の形で\n")
        return 2
    img = Image.new("RGB", (w, h), a.bg)
    d = ImageDraw.Draw(img)
    pad = int(w * 0.08)
    f_label = load_font(a.font, int(h * 0.035))
    f_title = load_font(a.font, int(h * 0.09))
    f_sub = load_font(a.font, int(h * 0.04))
    d.rectangle([pad, pad, pad + int(w * 0.08), pad + int(h * 0.008)], fill=a.accent)
    d.text((pad, pad + int(h * 0.03)), a.label.upper(), font=f_label, fill=a.accent)
    y = int(h * 0.32)
    for line in wrap(d, a.title, f_title, w - pad * 2)[:4]:
        d.text((pad, y), line, font=f_title, fill=a.fg)
        y += int(h * 0.11)
    d.text((pad, h - pad - int(h * 0.11)), a.date, font=f_sub, fill=a.fg)
    if a.sub:
        d.text((pad, h - pad - int(h * 0.055)), a.sub, font=f_sub, fill=a.accent)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    img.save(a.out, "PNG")
    print(f"{a.out} を作りました（{w}x{h}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
