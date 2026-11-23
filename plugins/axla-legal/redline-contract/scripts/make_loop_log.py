"""ループ記録（利用側のリポジトリの loop/legal/contracts/<契約 ID>/loop-log.md）の Google ドキュメント用 HTML を、JSON から作る。

使い方:
    python -I make_loop_log.py <log.json> <out.html>

log.json の形（例）:
{
  "title": "ループ記録（社内用・送付しない）",
  "lead": "契約：…",
  "sections": [
    {"h": 2, "title": "いまの状態と次の一手",
     "blocks": [
       {"table": {"head": ["項目", "中身"], "rows": [["状態", "…"]]}},
       {"p": "…"},
       {"ul": ["…", "…"]},
       {"json": {...}}
     ]}
  ],
  "appendix": {
    "title": "付録：境目の版と最新の直しの違い",
    "note": "…",
    "base": {"label": "最新の直し", "path": "その版の gdoc（F_vX.Y.Z_<自社名> Comments）から書き出した .docx（変更をすべて承諾したもの）か .txt／.md"},
    "versions": [{"label": "v1", "path": "F_vX.1.0_<相手> Original.docx"}, {"label": "v3", "path": "F_v3_<相手> ….docx"}]
  }
}
- p・ul・表のセルの文字列は HTML としてそのまま入れる（<b> や <br> が使える）。自分で書いた文だけを入れること。
- 付録は、各版と base を段落ごとに比べ、違う段落だけを表にする（同じ段落は base と同じ、と読む）。
- versions には、相手との境目の版（v1、v3 …）を入れる。社内の周回ごとの状態はファイルにしない。周回どうしを比べたいときは、
  その版の gdoc の版の履歴から、その時点の .docx を書き出して使う（使い終わったら手元から消す）。
"""
import difflib
import html
import json
import re
import sys
import zipfile


def paras(path):
    if path.endswith('.docx'):
        x = zipfile.ZipFile(path).read('word/document.xml').decode('utf-8')
        out = []
        for p in re.findall(r'<w:p\b(?:(?!<w:p\b).)*?</w:p>', x, flags=re.S):
            t = html.unescape(''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', p))).strip()
            if t:
                out.append(t)
        return out
    return [re.sub(r'^#+ ', '', l).strip() for l in open(path, encoding='utf-8') if l.strip()]


def table(head, rows):
    h = ''.join(f'<th>{html.escape(c)}</th>' for c in head)
    b = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<table border="1" cellpadding="4"><tr>{h}</tr>{b}</table>'


def block(b):
    if 'p' in b:
        return f'<p>{b["p"]}</p>'
    if 'ul' in b:
        return '<ul>' + ''.join(f'<li>{i}</li>' for i in b['ul']) + '</ul>'
    if 'table' in b:
        return table(b['table']['head'], b['table']['rows'])
    if 'json' in b:
        return '<pre>' + html.escape(json.dumps(b['json'], ensure_ascii=False, indent=1)) + '</pre>'
    raise SystemExit(f'知らない block: {list(b)}')


log = json.load(open(sys.argv[1], encoding='utf-8'))
P = [f'<h1>{html.escape(log["title"])}</h1>']
if log.get('lead'):
    P.append(f'<p>{log["lead"]}</p>')
for s in log.get('sections', []):
    h = s.get('h', 2)
    P.append(f'<h{h}>{html.escape(s["title"])}</h{h}>')
    P += [block(b) for b in s.get('blocks', [])]

ax = log.get('appendix')
if ax:
    P.append(f'<h2>{html.escape(ax["title"])}</h2>')
    if ax.get('note'):
        P.append(f'<p>{ax["note"]}</p>')
    base = paras(ax['base']['path'])
    bl = ax['base']['label']
    for v in ax['versions']:
        a = paras(v['path'])
        rows = []
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, base, autojunk=False).get_opcodes():
            if t != 'equal':
                rows.append(['<br>'.join(html.escape(s) for s in a[i1:i2]) or '（なし）',
                             '<br>'.join(html.escape(s) for s in base[j1:j2]) or '（なし）'])
        P.append(f'<h3>{html.escape(v.get("title", v["label"]))}</h3>')
        P.append(table([f'{v["label"]} の段落', f'{bl} の段落'], rows))

open(sys.argv[2], 'w', encoding='utf-8').write(
    '<html><head><meta charset="utf-8"></head><body>' + ''.join(P) + '</body></html>')
print('ok')
