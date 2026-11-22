"""相手に送る「清書」を作る。変更履歴とコメントを入れた展開済み .docx を、その場で清書にする。

使い方:
    python3 -I make_clean.py <unpacked_dir> [--date 2026-01-01T00:00:00Z]

すること:
1. 変更をすべて反映する（accept.py と同じ。取り消し線は残らない）。
2. コメントを外す（本文の範囲の印と参照、comments*.xml などの部品、その関係づけと Content_Types の登録）。
3. 作成者などの情報を消す（core.xml の作成者・最終更新者・表題・件名・キーワード・説明・最終印刷日、
   app.xml の会社・管理者、custom.xml の独自のプロパティ）。core.xml の更新日時は --date にする。

相手に送るのは清書だけ。変更履歴とコメント入りの版は、社内用の gdoc（F_vX.Y.Z_Axla Comments）に残す。
何を直したか・理由は、make_reply.py が作るメール本文の一覧で伝える。
"""
import argparse
import os
import re
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument('unpacked')
ap.add_argument('--date', help='core.xml の更新日時（UTC）。省くと元のまま')
args = ap.parse_args()
d = args.unpacked
here = os.path.dirname(os.path.abspath(__file__))

# 1. 変更をすべて反映する
subprocess.run([sys.executable, '-I', os.path.join(here, 'accept.py'), d], check=True, capture_output=True)


def rw(path, fn):
    p = os.path.join(d, path)
    if os.path.exists(p):
        t = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(fn(t))


# 2. コメントを外す
def strip_comment_marks(x):
    x = re.sub(r'<w:commentRange(?:Start|End) [^>]*/>', '', x)
    x = re.sub(r'<w:r>(?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:commentReference [^>]*/></w:r>', '', x, flags=re.S)
    x = re.sub(r'<w:commentReference [^>]*/>', '', x)
    return x


rw('word/document.xml', strip_comment_marks)
parts = ['comments.xml', 'commentsExtended.xml', 'commentsIds.xml', 'commentsExtensible.xml', 'people.xml']
for name in parts:
    p = os.path.join(d, 'word', name)
    if os.path.exists(p):
        os.remove(p)
rw('word/_rels/document.xml.rels',
   lambda t: re.sub(r'<Relationship [^>]*Target="(?:%s)"[^>]*/>' % '|'.join(re.escape(n) for n in parts), '', t))
rw('[Content_Types].xml',
   lambda t: re.sub(r'<Override [^>]*PartName="/word/(?:%s)"[^>]*/>' % '|'.join(re.escape(n) for n in parts), '', t))


# 3. 作成者などの情報を消す
def clean_core(t):
    for tag in ['dc:title', 'dc:subject', 'dc:creator', 'cp:keywords', 'dc:description', 'cp:lastModifiedBy', 'cp:category']:
        t = re.sub(r'<%s>[^<]*</%s>' % (tag, tag), f'<{tag}></{tag}>', t)
    t = re.sub(r'<cp:lastPrinted>[^<]*</cp:lastPrinted>', '', t)
    t = re.sub(r'<cp:revision>[^<]*</cp:revision>', '<cp:revision>1</cp:revision>', t)
    if args.date:
        t = re.sub(r'(<dcterms:modified [^>]*>)[^<]*(</dcterms:modified>)', r'\g<1>' + args.date + r'\2', t)
    return t


rw('docProps/core.xml', clean_core)
rw('docProps/app.xml', lambda t: re.sub(r'<(Company|Manager)>[^<]*</\1>', r'<\1></\1>', t))
rw('docProps/custom.xml', lambda t: re.sub(r'<property\b.*?</property>', '', t, flags=re.S))

x = open(os.path.join(d, 'word/document.xml'), encoding='utf-8').read()
left = {k: len(re.findall(p, x)) for k, p in [('ins', r'<w:ins '), ('del', r'<w:del '), ('rPrChange', r'<w:rPrChange'), ('comment', r'<w:comment(?:Range|Reference)')]}
if any(left.values()):
    sys.exit(f'清書に残っている：{left}')
print('ok: 変更履歴 0・コメント 0・作成者などの情報を消した')
