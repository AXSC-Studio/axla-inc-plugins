"""展開済み .docx の変更履歴をすべて承諾した版にする（その場で書き換える）。

使い方:
    python -I accept.py <unpacked_dir>

- 削除（w:del）は中身ごと消し、追加（w:ins）は印だけ外す。
- 段落の印が削除で、承諾後に文字が残らない段落は、段落ごと消す。
- settings.xml の変更履歴の記録（trackRevisions）を外す（settings.xml が無ければ飛ばす）。
コメントは残る。
"""
import os
import re
import sys

d = sys.argv[1]
f = d + '/word/document.xml'
x = open(f, encoding='utf-8').read()


def drop_deleted_paragraph(m):
    p = m.group(0)
    ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, flags=re.S)
    if not ppr or not re.search(r'<w:rPr>(?:(?!</w:rPr>).)*<w:del [^>]*/>', ppr.group(0), flags=re.S):
        return p
    rest = re.sub(r'<w:del [^>]*>.*?</w:del>', '', p, flags=re.S)
    left = ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', rest))
    return '' if not left.strip() else p


x = re.sub(r'<w:p\b(?:(?!<w:p\b).)*?</w:p>', drop_deleted_paragraph, x, flags=re.S)
x = re.sub(r'<w:rPrChange [^>]*>.*?</w:rPrChange>', '', x, flags=re.S)  # 書式の変更履歴は、新しい書式を残す
x = re.sub(r'<w:(ins|del) [^>]*/>', '', x)
x = re.sub(r'<w:del [^>]*>.*?</w:del>', '', x, flags=re.S)
x = re.sub(r'<w:ins [^>]*>(.*?)</w:ins>', r'\1', x, flags=re.S)
x = x.replace('<w:rPr></w:rPr>', '')
open(f, 'w', encoding='utf-8').write(x)
s = d + '/word/settings.xml'
if os.path.exists(s):  # Word 以外のソフトで作った文書には、settings.xml が無いことがある
    y = open(s, encoding='utf-8').read()
    open(s, 'w', encoding='utf-8').write(y.replace('<w:trackRevisions/>', ''))
print('ok')
