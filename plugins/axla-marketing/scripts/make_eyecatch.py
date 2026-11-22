"""文字だけのアイキャッチを作る（無料。外の API を呼ばない）。

使い方:
    python3 -I make_eyecatch.py --title "<題>" --date yyyy-mm-dd --config <loop/meet-to-article/config.json> --out eyecatch.png

config.json の eyecatch:
    {"size": [1200, 630], "bg": "#111111", "fg": "#ffffff", "accent": "#c8a96a",
     "label": "COLUMN", "font": "<日本語が出るフォントのパス>"}
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_FONTS = [
    '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc',
]


def font(path, size):
    for p in [path, *DEFAULT_FONTS]:
        if p and Path(p).exists():
            return ImageFont.truetype(p, size)
    raise SystemExit('日本語のフォントが見つかりません。config の eyecatch.font にパスを書いてください')


def wrap(draw, text, f, width):
    lines, cur = [], ''
    for ch in text:
        if draw.textlength(cur + ch, font=f) > width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    return lines + ([cur] if cur else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--title', required=True)
    ap.add_argument('--date', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    c = json.loads(Path(a.config).read_text(encoding='utf-8')).get('eyecatch', {})
    w, h = c.get('size', [1200, 630])
    pad = int(w * 0.07)
    img = Image.new('RGB', (w, h), c.get('bg', '#111111'))
    d = ImageDraw.Draw(img)

    small = font(c.get('font'), int(h * 0.05))
    d.text((pad, pad), c.get('label', 'COLUMN'), font=small, fill=c.get('accent', '#c8a96a'))
    d.text((pad, h - pad - small.size), a.date.replace('-', '.'), font=small, fill=c.get('fg', '#ffffff'))

    # 題：入る大きさまで小さくする（最大3行）
    size = int(h * 0.11)
    while True:
        big = font(c.get('font'), size)
        lines = wrap(d, a.title, big, w - pad * 2)
        if len(lines) <= 3 or size <= 24:
            break
        size -= 4
    lh = int(size * 1.35)
    y = (h - lh * len(lines)) // 2
    for line in lines:
        d.text((pad, y), line, font=big, fill=c.get('fg', '#ffffff'))
        y += lh
    d.rectangle([pad, y + lh // 4, pad + int(w * 0.08), y + lh // 4 + 6], fill=c.get('accent', '#c8a96a'))

    img.save(a.out)
    print(f'アイキャッチ: {a.out}（{w}x{h}）')


if __name__ == '__main__':
    main()
