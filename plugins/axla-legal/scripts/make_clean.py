"""相手に送る「清書」の .docx を作る。変更履歴とコメントを入れた展開済み .docx から、清書を1つのファイルにする。

使い方:
    python3 -I make_clean.py <unpacked_dir> --out <clean.docx> [--date 2026-01-01T00:00:00Z] [--record <契約の記録フォルダ>]

すること:
1. 展開済みのフォルダを作業用の一時フォルダに写す（元のフォルダは書き換えない）。
2. 変更をすべて反映する（accept.py と同じ。取り消し線は残らない）。
3. コメントを外す（本文の範囲の印と参照、comments*.xml などの部品、その関係づけと Content_Types の登録）。
4. 作成者などの情報を消す（core.xml の作成者・最終更新者・表題・件名・キーワード・説明・分類・最終印刷日、
   app.xml の会社・管理者、custom.xml の独自のプロパティ）。core.xml の更新日時は --date にする。
5. 清書になっているかを自分で確かめる（変更履歴 0・コメントの印と部品 0・隠し文字 0・作成者などの情報が空）。
6. 通ったときだけ、--out に .docx を書く（同じ入力と --date なら、バイト単位で同じファイルになる）。
7. --record を渡すと、契約の gate.json の clean に「通った・清書の sha256・時刻」を書く。
   Hook は、この記録が無いと、その契約の返信の下書きを作らせない。

1つでも通らなければ、終了コード 1 で止まり、--out のファイルは残さない（前からあったものも消す）。
--record を渡したときは、gate.json の clean も「通っていない」に書き換える。
相手に送るのは清書だけ。変更履歴とコメント入りの版は、社内用の gdoc（F_vX.Y.Z_Axla Comments）に残す。
何を直したか・理由は、make_reply.py が作るメール本文の一覧で伝える。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

COMMENT_PARTS = ['comments.xml', 'commentsExtended.xml', 'commentsIds.xml', 'commentsExtensible.xml', 'people.xml']
# 本文の部品（変更履歴・コメントの印・隠し文字を調べる所）
BODY_PART = re.compile(r'^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$')
REVISION = re.compile(r'<w:(ins|del|moveFrom|moveTo|moveFromRangeStart|moveToRangeStart|cellIns|cellDel|cellMerge|'
                      r'rPrChange|pPrChange|sectPrChange|tblPrChange|tblGridChange|tcPrChange|trPrChange|numberingChange)\b')
COMMENT_MARK = re.compile(r'<w:comment(?:RangeStart|RangeEnd|Reference)\b')
HIDDEN = re.compile(r'<w:vanish\b')
CORE_TAGS = ['dc:title', 'dc:subject', 'dc:creator', 'cp:keywords', 'dc:description', 'cp:lastModifiedBy', 'cp:category']
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def read(d, path):
    p = os.path.join(d, path)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None


def rw(d, path, fn):
    t = read(d, path)
    if t is not None:
        open(os.path.join(d, path), 'w', encoding='utf-8').write(fn(t))


def strip_comment_marks(x):
    x = re.sub(r'<w:commentRange(?:Start|End) [^>]*/>', '', x)
    x = re.sub(r'<w:r>(?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:commentReference [^>]*/></w:r>', '', x, flags=re.S)
    x = re.sub(r'<w:commentReference [^>]*/>', '', x)
    return x


def clean(d, date):
    rw(d, 'word/document.xml', strip_comment_marks)
    for name in COMMENT_PARTS:
        p = os.path.join(d, 'word', name)
        if os.path.exists(p):
            os.remove(p)
    names = '|'.join(re.escape(n) for n in COMMENT_PARTS)
    rw(d, 'word/_rels/document.xml.rels', lambda t: re.sub(r'<Relationship [^>]*Target="(?:%s)"[^>]*/>' % names, '', t))
    rw(d, '[Content_Types].xml', lambda t: re.sub(r'<Override [^>]*PartName="/word/(?:%s)"[^>]*/>' % names, '', t))

    def clean_core(t):
        for tag in CORE_TAGS:
            t = re.sub(r'<%s>[^<]*</%s>' % (tag, tag), f'<{tag}></{tag}>', t)
        t = re.sub(r'<cp:lastPrinted>[^<]*</cp:lastPrinted>', '', t)
        t = re.sub(r'<cp:revision>[^<]*</cp:revision>', '<cp:revision>1</cp:revision>', t)
        if date:
            t = re.sub(r'(<dcterms:modified [^>]*>)[^<]*(</dcterms:modified>)', r'\g<1>' + date + r'\2', t)
        return t

    rw(d, 'docProps/core.xml', clean_core)
    rw(d, 'docProps/app.xml', lambda t: re.sub(r'<(Company|Manager)>[^<]*</\1>', r'<\1></\1>', t))
    rw(d, 'docProps/custom.xml', lambda t: re.sub(r'<property\b.*?</property>', '', t, flags=re.S))


def files_of(d):
    out = []
    for root, _, fs in os.walk(d):
        for f in fs:
            out.append(os.path.relpath(os.path.join(root, f), d).replace(os.sep, '/'))
    return sorted(out, key=lambda p: (p != '[Content_Types].xml', p))


def verify(d):
    """清書になっていない所を、短い説明のリストで返す（空なら合格）。"""
    bad = []
    for path in files_of(d):
        if BODY_PART.match(path):
            x = read(d, path)
            for label, pat in [('変更履歴', REVISION), ('コメントの印', COMMENT_MARK), ('隠し文字', HIDDEN)]:
                n = len(pat.findall(x))
                if n:
                    bad.append(f'{path}：{label} {n}')
        if path.startswith('word/') and os.path.basename(path) in COMMENT_PARTS:
            bad.append(f'{path}：コメントの部品が残っている')
    rels = read(d, 'word/_rels/document.xml.rels') or ''
    if re.search(r'Target="(?:%s)"' % '|'.join(re.escape(n) for n in COMMENT_PARTS), rels):
        bad.append('word/_rels/document.xml.rels：コメントの部品への関係づけが残っている')
    core = read(d, 'docProps/core.xml') or ''
    for tag in CORE_TAGS:
        m = re.search(r'<%s>([^<]+)</%s>' % (tag, tag), core)
        if m and m.group(1).strip():
            bad.append(f'docProps/core.xml：{tag} が空でない')
    app = read(d, 'docProps/app.xml') or ''
    for tag in ['Company', 'Manager']:
        m = re.search(r'<%s>([^<]+)</%s>' % (tag, tag), app)
        if m and m.group(1).strip():
            bad.append(f'docProps/app.xml：{tag} が空でない')
    if re.search(r'<property\b', read(d, 'docProps/custom.xml') or ''):
        bad.append('docProps/custom.xml：独自のプロパティが残っている')
    return bad


def pack(d, dest):
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in files_of(d):
            info = zipfile.ZipInfo(path, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, open(os.path.join(d, path), 'rb').read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('unpacked', help='変更履歴とコメントを入れた展開済みの .docx のフォルダ（書き換えない）')
    ap.add_argument('--out', required=True, help='清書の .docx を書く場所')
    ap.add_argument('--date', help='core.xml の更新日時（UTC）。省くと元のまま')
    ap.add_argument('--record', help='契約の記録フォルダ（loop/legal/contracts/<契約 ID>）。gate.json に結果を書く')
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    if os.path.exists(out):
        os.remove(out)  # 前の清書が残っていると、失敗に気づかず送ってしまうため
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import gate
    if args.record:
        gate.update(args.record, 'clean', {'ok': False, 'at': gate.now()})
    tmp = tempfile.mkdtemp(prefix='make_clean_')
    part = out + '.part'
    try:
        d = os.path.join(tmp, 'u')
        shutil.copytree(args.unpacked, d)
        r = subprocess.run([sys.executable, '-I', os.path.join(here, 'accept.py'), d], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('止めた：変更の反映（accept.py）が失敗した。清書は作っていない。\n' + r.stderr.strip())
        clean(d, args.date)
        bad = verify(d)
        if bad:
            sys.exit('止めた：清書の検査に通らない。清書は作っていない。\n- ' + '\n- '.join(bad))
        pack(d, part)
        os.replace(part, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if os.path.exists(part):
            os.remove(part)
    if args.record:
        gate.update(args.record, 'clean', {'ok': True, 'sha256': gate.sha256(out), 'file': os.path.basename(out), 'at': gate.now()})
    print(f'ok: 変更履歴 0・コメント 0・隠し文字 0・作成者などの情報を消した → {out}')


if __name__ == '__main__':
    main()
