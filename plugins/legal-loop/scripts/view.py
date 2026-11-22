"""展開済み .docx の本文を段落ごとに表示する。

使い方:
    python -I view.py <unpacked_dir> redline   # [-削除-]{+追加+} の形で、変更のある段落も含めて全部
    python -I view.py <unpacked_dir> changed   # 変更のある段落だけ
    python -I view.py <unpacked_dir> accept    # 変更をすべて承諾したときの本文
"""
import html
import re
import sys

x = open(sys.argv[1] + '/word/document.xml', encoding='utf-8').read()
mode = sys.argv[2]
body = x[x.index('<w:body>'):]
for p in re.findall(r'<w:p\b(?:(?!<w:p\b).)*?</w:p>', body, flags=re.S):
    ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, flags=re.S)
    pdel = bool(ppr and re.search(r'<w:rPr>(?:(?!</w:rPr>).)*<w:del [^>]*/>', ppr.group(0), flags=re.S))
    out, changed = '', False
    for m in re.finditer(r'<w:del [^>]*>(.*?)</w:del>|<w:ins [^>]*>(.*?)</w:ins>|<w:r(?: [^>]*)?>(.*?)</w:r>', p, flags=re.S):
        d, i, r = m.groups()
        if d is not None:
            changed = True
            t = ''.join(re.findall(r'<w:delText[^>]*>([^<]*)<', d))
            out += f'[-{t}-]' if mode != 'accept' else ''
        elif i is not None:
            changed = True
            t = ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)<', i))
            out += f'{{+{t}+}}' if mode != 'accept' else t
        else:
            out += ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)<', r))
    out = html.unescape(out)
    if mode == 'accept' and pdel and not out.strip():
        continue
    if mode == 'changed' and not changed:
        continue
    if out.strip():
        print(out)
