"""展開済み、または .docx の形式を確かめる（Issue #8。外のスキルの validate.py の代わり。標準ライブラリだけ）。

使い方:
    python3 -I validate_docx.py <展開済みのフォルダ か .docx>

確かめること（1つでも違えば終了コード 1）:
1. すべての .xml と .rels が XML として読める（DOCTYPE・ENTITY の入ったものは、読まずに止める）
2. 関係づけ（.rels）の指す部品があり、[Content_Types].xml に本文の登録がある
3. コメント：本文の commentReference と comments.xml の w:comment の ID が1対1で対応し、範囲の印の始まりと終わりがそろう
4. 変更履歴（w:ins・w:del など）の w:id が重なっていない
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

REV = re.compile(r'<w:(ins|del|moveFrom|moveTo|\w+PrChange)\b[^>]*\bw:id="(\d+)"')


def load(src):
    if os.path.isdir(src):
        out = {}
        for root, _, files in os.walk(src):
            for n in files:
                p = os.path.join(root, n)
                out[os.path.relpath(p, src).replace(os.sep, '/')] = open(p, 'rb').read()
        return out
    with zipfile.ZipFile(src) as z:
        return {n: z.read(n) for n in z.namelist() if not n.endswith('/')}


def check(parts):
    bad = []
    texts = {}
    for name, data in parts.items():
        if not name.endswith(('.xml', '.rels')):
            continue
        s = data.decode('utf-8', errors='replace')
        if re.search(r'<!DOCTYPE|<!ENTITY', s):
            bad.append(f'{name}：DOCTYPE／ENTITY がある（読まない）')
            continue
        try:
            ET.fromstring(data)
        except ET.ParseError as e:
            bad.append(f'{name}：XML として読めない（{e}）')
            continue
        texts[name] = s
    if 'word/document.xml' not in texts:
        bad.append('word/document.xml が無いか読めない')
        return bad
    ct = texts.get('[Content_Types].xml', '')
    if 'PartName="/word/document.xml"' not in ct:
        bad.append('[Content_Types].xml に本文（/word/document.xml）の登録が無い')
    for rels, s in texts.items():
        if not rels.endswith('.rels'):
            continue
        base = os.path.dirname(os.path.dirname(rels))
        for m in re.finditer(r'<Relationship\b[^>]*>', s):
            tag = m.group(0)
            if 'TargetMode="External"' in tag:
                continue
            t = re.search(r'Target="([^"]+)"', tag)
            if not t:
                continue
            target = t.group(1).lstrip('/') if t.group(1).startswith('/') else os.path.normpath(os.path.join(base, t.group(1))).replace(os.sep, '/')
            if target not in parts:
                bad.append(f'{rels}：無い部品 {target} を指している')
    body = texts['word/document.xml']
    refs = re.findall(r'<w:commentReference\b[^>]*\bw:id="(\d+)"', body)
    starts = re.findall(r'<w:commentRangeStart\b[^>]*\bw:id="(\d+)"', body)
    ends = re.findall(r'<w:commentRangeEnd\b[^>]*\bw:id="(\d+)"', body)
    com = re.findall(r'<w:comment\b[^>]*\bw:id="(\d+)"', texts.get('word/comments.xml', ''))
    if sorted(refs) != sorted(set(refs)):
        bad.append('本文のコメントの参照に、同じ ID が2回ある')
    if set(refs) != set(com):
        bad.append(f'コメントの参照と本体が合わない（本文だけ：{sorted(set(refs) - set(com))}、本体だけ：{sorted(set(com) - set(refs))}）')
    if sorted(starts) != sorted(ends):
        bad.append('コメントの範囲の印（始まりと終わり）がそろわない')
    if com and 'word/comments.xml' in texts and 'PartName="/word/comments.xml"' not in ct:
        bad.append('[Content_Types].xml に comments.xml の登録が無い')
    ids = [m.group(2) for name, s in texts.items() if name.startswith('word/') for m in REV.finditer(s)]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        bad.append(f'変更履歴の ID が重なっている：{dup[:10]}')
    return bad


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    bad = check(load(sys.argv[1]))
    for b in bad:
        print('NG：' + b)
    print('ok: 形式は正しい' if not bad else f'{len(bad)} 件の問題')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
