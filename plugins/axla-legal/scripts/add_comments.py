"""変更履歴を入れた展開済み .docx に、changes JSON の "comments" を Word のコメントとして入れる。

使い方:
    python add_comments.py <unpacked_dir> <changes.json> --comment-py <comment.py のパス> \
        [--author "<作成者名>"] [--initials <頭文字>] [--comment-id-start N]

--author／--initials を省くと、changes JSON の "author"／"initials"、それもなければ利用側の loop/legal/config.json の値を使う。
作成者名がどれにも無ければ止まる（作成者名をコードに決め打ちしない。Issue #5）。
--comment-id-start を省くと、原本にある既存のコメントの ID の最大＋1 から振る（なければ 0）。

コメントの本体（comments.xml・commentsExtended.xml・commentsExtensible.xml・commentsIds.xml の4つの部品と、
その関係づけ）は comment.py（docx スキル付属。README の「入手先」）が書く。
このスクリプトは、本文の該当段落に範囲の印（commentRangeStart／End）と参照を置く。
comment.py は defusedxml を使うので、README の venv の python で実行する。

先に、コメントを付ける段落がすべてあるかを確かめる。作業は写しで行い、全部うまくいったときだけ元と入れ替える
（途中で落ちても、コメントだけが残った半端な文書にならない）。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument('unpacked')
ap.add_argument('changes')
ap.add_argument('--comment-py', required=True)
ap.add_argument('--author')
ap.add_argument('--initials')
ap.add_argument('--comment-id-start', type=int)
args = ap.parse_args()

spec = json.load(open(args.changes, encoding='utf-8'))
comments = spec.get('comments', [])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402
cfg = gate.load_config(os.path.abspath(args.changes))
author = args.author or spec.get('author') or cfg.get('author')
initials = args.initials if args.initials is not None else spec.get('initials', cfg.get('initials', ''))
if not author:
    sys.exit('作成者名がない：--author か、changes JSON の "author" か、利用側の loop/legal/config.json の "author" に書く')
start_id = args.comment_id_start
if start_id is None:
    cx = args.unpacked + '/word/comments.xml'
    ids = [int(i) for i in re.findall(r'<w:comment [^>]*w:id="(\d+)"', open(cx, encoding='utf-8').read())] if os.path.exists(cx) else []
    start_id = max(ids) + 1 if ids else 0
if not os.path.isfile(args.comment_py):
    sys.exit(f'止まる：comment.py が無い：{args.comment_py}（README の「入手先」）')
src = os.path.abspath(args.unpacked)
with open(os.path.join(src, 'word', 'document.xml'), encoding='utf-8') as fh:
    x0 = fh.read()
missing = sorted({p for c in comments for p in (c['start'], c.get('end') or c['start'])
                  if not re.search(r'w14:paraId="%s"' % re.escape(p), x0)})
if missing:
    sys.exit(f'止まる：コメントを付ける段落が見つからない：{", ".join(missing)}（何も書いていない）')
tmp = tempfile.mkdtemp(prefix='add_comments_')
work = os.path.join(tmp, 'u')
shutil.copytree(src, work)
f = work + '/word/document.xml'


def open_empty(x, pid):
    """`<w:p …/>` の1つのタグで閉じた空の段落を、`<w:p …></w:p>` に開く（印を中に置けるように）。"""
    return re.sub(r'(<w:p\b[^>]*?w14:paraId="%s"[^>]*?)/>' % re.escape(pid), r'\1></w:p>', x, count=1)


for k, c in enumerate(comments):
    n = start_id + k
    start, end, text = c['start'], c.get('end') or c['start'], c['text']
    cmd = [sys.executable, args.comment_py, work, text, '--id', str(n), '--author', author]
    if initials:
        cmd += ['--initials', initials]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f'止まる：comment.py が {k + 1} 件目で失敗した（何も書いていない）。\n' + (r.stderr or r.stdout).strip()[-800:])
    x = open(f, encoding='utf-8').read()
    x = open_empty(x, start)
    x = open_empty(x, end)
    # 始まり：段落の pPr の直後
    m = re.search(r'<w:p\b[^>]*?w14:paraId="%s"[^>]*?>(<w:pPr>.*?</w:pPr>)?' % re.escape(start), x, flags=re.S)
    if not m:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f'段落が見つからない: {start}')
    x = x[:m.end()] + f'<w:commentRangeStart w:id="{n}"/>' + x[m.end():]
    # 終わり：段落の </w:p> の直前。参照のランに文字スタイルは付けない（雛形に定義がないことが多い）
    m = re.search(r'<w:p\b[^>]*?w14:paraId="%s"[^>]*?>.*?(</w:p>)' % re.escape(end), x, flags=re.S)
    if not m:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f'段落が見つからない: {end}')
    ref = f'<w:commentRangeEnd w:id="{n}"/><w:r><w:commentReference w:id="{n}"/></w:r>'
    x = x[:m.start(1)] + ref + x[m.start(1):]
    open(f, 'w', encoding='utf-8').write(x)
# 全部うまくいったので、元と入れ替える
bak = src + '.bak_add_comments'
os.replace(src, bak)
shutil.move(work, src)
shutil.rmtree(bak)
shutil.rmtree(tmp, ignore_errors=True)
print('comments:', len(comments))
