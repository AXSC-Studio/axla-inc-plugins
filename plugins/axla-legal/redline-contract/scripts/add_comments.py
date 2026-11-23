"""変更履歴を入れた展開済み .docx に、changes JSON の "comments" を Word のコメントとして入れる。

使い方:
    python3 -I add_comments.py <unpacked_dir> <changes.json> [--author "<作成者名>"] [--initials <頭文字>] [--comment-id-start N]

--author／--initials を省くと、changes JSON の "author"／"initials"、それもなければ利用側の loop/legal/config.json の値を使う。
作成者名がどれにも無ければ止まる（作成者名をコードに決め打ちしない。Issue #5）。
--comment-id-start を省くと、原本にある既存のコメントの ID の最大＋1 から振る（なければ 0）。
コメントの日時は changes JSON の "date"（無ければ実行時刻）。同じ JSON からは、同じ部品になる。

標準ライブラリだけで動く（Issue #8・#9。外のスキルの部品も venv も使わない）。書くもの：
- word/comments.xml（コメントの本体。原本に前からあれば、その後ろに足す）
- word/_rels/document.xml.rels のコメントの関係づけと、[Content_Types].xml の登録（無ければ足す）
- 本文の該当段落の、範囲の印（commentRangeStart／End）と参照（commentReference）

先に、コメントを付ける段落がすべてあるかを確かめる。全部の部品を作り直せてから、まとめて書く
（途中で落ちても、コメントだけが残った半端な文書にならない）。
"""
import argparse
import datetime
import json
import os
import re
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
REL_TYPE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
CT_COMMENTS = 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml'


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def comment_xml(n, author, initials, date, text):
    paras = ''.join(f'<w:p><w:r><w:t xml:space="preserve">{escape(line)}</w:t></w:r></w:p>'
                    for line in (text.split('\n') or ['']))
    ini = f' w:initials="{escape(initials, {chr(34): "&quot;"})}"' if initials else ''
    return (f'<w:comment w:id="{n}" w:author="{escape(author, {chr(34): "&quot;"})}" w:date="{date}"{ini}>'
            f'{paras}</w:comment>')


def open_empty(x, pid):
    """`<w:p …/>` の1つのタグで閉じた空の段落を、`<w:p …></w:p>` に開く（印を中に置けるように）。"""
    return re.sub(r'(<w:p\b[^>]*?w14:paraId="%s"[^>]*?)/>' % re.escape(pid), r'\1></w:p>', x, count=1)


def place_marks(x, n, start, end):
    x = open_empty(open_empty(x, start), end)
    m = re.search(r'<w:p\b[^>]*?w14:paraId="%s"[^>]*?>(<w:pPr>.*?</w:pPr>)?' % re.escape(start), x, flags=re.S)
    if not m:
        sys.exit(f'止まる：段落が見つからない: {start}（何も書いていない）')
    x = x[:m.end()] + f'<w:commentRangeStart w:id="{n}"/>' + x[m.end():]
    m = re.search(r'<w:p\b[^>]*?w14:paraId="%s"[^>]*?>.*?(</w:p>)' % re.escape(end), x, flags=re.S)
    if not m:
        sys.exit(f'止まる：段落が見つからない: {end}（何も書いていない）')
    # 参照のランに文字スタイルは付けない（雛形に定義がないことが多い）
    ref = f'<w:commentRangeEnd w:id="{n}"/><w:r><w:commentReference w:id="{n}"/></w:r>'
    return x[:m.start(1)] + ref + x[m.start(1):]


def add_rel(rels):
    if re.search(r'Target="comments\.xml"', rels):
        return rels
    ids = [int(i) for i in re.findall(r'Id="rId(\d+)"', rels)]
    rid = f'rId{max(ids, default=0) + 1}'
    return rels.replace('</Relationships>', f'<Relationship Id="{rid}" Type="{REL_TYPE}" Target="comments.xml"/></Relationships>')


def add_ct(ct):
    if 'PartName="/word/comments.xml"' in ct:
        return ct
    return ct.replace('</Types>', f'<Override PartName="/word/comments.xml" ContentType="{CT_COMMENTS}"/></Types>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('unpacked')
    ap.add_argument('changes')
    ap.add_argument('--author')
    ap.add_argument('--initials')
    ap.add_argument('--comment-id-start', type=int)
    args = ap.parse_args()

    with open(args.changes, encoding='utf-8') as f:
        spec = json.load(f)
    comments = spec.get('comments', [])
    cfg = gate.load_config(os.path.abspath(args.changes))
    author = args.author or spec.get('author') or cfg.get('author')
    initials = args.initials if args.initials is not None else spec.get('initials', cfg.get('initials', ''))
    if not author:
        sys.exit('作成者名がない：--author か、changes JSON の "author" か、利用側の loop/legal/config.json の "author" に書く')
    date = spec.get('date') or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    d = os.path.abspath(args.unpacked)
    paths = {k: os.path.join(d, *v) for k, v in {
        'doc': ('word', 'document.xml'), 'com': ('word', 'comments.xml'),
        'rels': ('word', '_rels', 'document.xml.rels'), 'ct': ('[Content_Types].xml',)}.items()}
    for k in ('doc', 'rels', 'ct'):
        if not os.path.isfile(paths[k]):
            sys.exit(f'止まる：{paths[k]} が無い（展開済みの .docx のフォルダを渡す）')
    x = read(paths['doc'])
    missing = sorted({p for c in comments for p in (c['start'], c.get('end') or c['start'])
                      if not re.search(r'w14:paraId="%s"' % re.escape(p), x)})
    if missing:
        sys.exit(f'止まる：コメントを付ける段落が見つからない：{", ".join(missing)}（何も書いていない）')

    com = read(paths['com']) if os.path.exists(paths['com']) else \
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:comments xmlns:w="{W_NS}"></w:comments>'
    if '</w:comments>' not in com:  # 空の要素 <w:comments …/> で書かれていることもある
        com = re.sub(r'<w:comments\b([^>]*)/>', r'<w:comments\1></w:comments>', com)
    used = [int(i) for i in re.findall(r'<w:comment\b[^>]*\bw:id="(\d+)"', com)]
    start_id = args.comment_id_start if args.comment_id_start is not None else (max(used) + 1 if used else 0)
    if set(range(start_id, start_id + len(comments))) & set(used):
        sys.exit(f'止まる：コメントの ID {start_id} からが、原本のコメントとぶつかる（何も書いていない）')

    new = []
    for k, c in enumerate(comments):
        n = start_id + k
        x = place_marks(x, n, c['start'], c.get('end') or c['start'])
        new.append(comment_xml(n, author, initials, date, c['text']))
    com = com.replace('</w:comments>', ''.join(new) + '</w:comments>')
    out = {paths['doc']: x, paths['com']: com, paths['rels']: add_rel(read(paths['rels'])), paths['ct']: add_ct(read(paths['ct']))}
    for p, t in out.items():  # 全部を作り直せてから書く
        with open(p, 'w', encoding='utf-8') as f:
            f.write(t)
    print('comments:', len(comments))


if __name__ == '__main__':
    main()
