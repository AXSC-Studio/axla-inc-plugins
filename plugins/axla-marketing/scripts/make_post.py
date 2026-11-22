"""編集役が書いた Markdown から、CMS の下書きの JSON を作る。

使い方:
    python3 -I make_post.py <article.md> --config <loop/meet-to-article/config.json> --out-dir <記事の JSON の置き場> [--date yyyy-mm-dd]

article.md の形は prompts/editor-prompts.md の「出すもの」。
- 1行目 `# 題`、次の段落がリード、`---` の後ろに `slug:` と `要確認:`
- 本文は段落・`## 見出し`・`**太字**` だけを HTML にする
同じ slug のファイルが既にあれば止める（上書きしない）。status は必ず draft。
要確認の部分は JSON に入れず、標準出力に出す（通知に使う）。
"""
import argparse
import html
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

SLUG = re.compile(r'^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$')


def parse(text):
    head, _, tail = text.partition('\n---\n')
    lines = head.strip().splitlines()
    if not lines or not lines[0].startswith('# '):
        sys.exit('1行目は「# 題」にしてください')
    title = lines[0][2:].strip()
    blocks = [b.strip() for b in '\n'.join(lines[1:]).strip().split('\n\n') if b.strip()]
    if not blocks:
        sys.exit('リードと本文がありません')
    excerpt, body = blocks[0], blocks[1:]
    m = re.search(r'^slug:\s*(\S+)', tail, re.M)
    if not m:
        sys.exit('--- の後ろに slug: がありません')
    review = tail.split('要確認:', 1)[1].strip() if '要確認:' in tail else ''
    return title, excerpt, body, m.group(1), review


def inline(s):
    s = html.escape(s, quote=False)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)


def to_html(blocks):
    out = []
    for b in blocks:
        if b.startswith('## '):
            head, _, b = b.partition('\n')
            out.append('<h2>' + inline(head[3:].strip()) + '</h2>')
            if not b.strip():
                continue
        out.append('<p>' + '<br>'.join(inline(x.strip()) for x in b.strip().splitlines()) + '</p>')
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article')
    ap.add_argument('--config', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--date', default=date.today().isoformat())
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding='utf-8'))
    title, excerpt, body, slug, review = parse(Path(a.article).read_text(encoding='utf-8'))
    if not SLUG.match(slug) or not slug.startswith(a.date):
        sys.exit(f'slug の形が違います（{a.date}-english-words、すべて小文字）: {slug}')

    plain = re.sub(r'\*\*|^## ', '', '\n'.join(body), flags=re.M)
    n = len(re.sub(r'\s', '', plain))
    lo, hi = cfg.get('length', [1500, 2500])
    if not lo <= n <= hi:
        sys.exit(f'本文が {n} 字です（{lo}〜{hi} 字にしてください）')

    out = Path(a.out_dir) / f'{slug}.json'
    if out.exists():
        sys.exit(f'既にあります。上書きしません: {out}')

    post = {
        'slug': slug,
        'title': title,
        'date': a.date,
        'category': cfg.get('category', 'column'),
        'sites': cfg.get('sites', []),
        'status': 'draft',
        'body': to_html(body),
        'excerpt': excerpt,
        'thumbnail': cfg.get('thumbnail_url', '').format(slug=slug),
        'externalUrl': '',
        'author': cfg.get('author', ''),
        'source': 'cms',
        'kind': 'news',
        'createdAt': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
    }
    out.write_text(json.dumps(post, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'下書き: {out}（{n} 字）')
    print('要確認:')
    print(review or '- なし')


if __name__ == '__main__':
    main()
