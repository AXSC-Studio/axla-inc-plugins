"""展開済み .docx の変更履歴をすべて承諾した版にする（その場で書き換える）。

使い方:
    python -I accept.py <unpacked_dir>

- 本文・ヘッダー・フッター・脚注・文末脚注（word/document.xml・header*.xml・footer*.xml・footnotes.xml・endnotes.xml）に効く。
- 削除（w:del）と移動元（w:moveFrom）は中身ごと消し、追加（w:ins）と移動先（w:moveTo）は印だけ外す。
- 書式・段落・表・節の変更履歴（*PrChange など）は、新しい書式を残して印を消す。
- 段落の印が削除で、承諾後に文字が残らない段落は、段落ごと消す。
- settings.xml の変更履歴の記録（trackRevisions）を外す（settings.xml が無ければ飛ばす）。
- 先に全部の部品を作り直してから書く。途中で読めない部品があれば、何も書かずに止まる。
コメントは残る（清書では make_clean.py が外す）。
"""
import os
import re
import sys

BODY_PART = re.compile(r'^(document|header\d*|footer\d*|footnotes|endnotes)\.xml$')


def drop_deleted_paragraph(m):
    p = m.group(0)
    ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, flags=re.S)
    if not ppr or not re.search(r'<w:rPr>(?:(?!</w:rPr>).)*<w:(?:del|moveFrom) [^>]*/>', ppr.group(0), flags=re.S):
        return p
    rest = re.sub(r'<w:(del|moveFrom) [^>]*>.*?</w:\1>', '', p, flags=re.S)
    left = ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', rest))
    return '' if not left.strip() else p


def accept(x):
    x = re.sub(r'<w:p\b(?:(?!<w:p\b).)*?</w:p>', drop_deleted_paragraph, x, flags=re.S)
    # 書式・段落・表・節などの変更履歴は、新しい書式を残す（印と古い書式を消す）
    x = re.sub(r'<w:(\w+PrChange|tblGridChange|numberingChange)\b[^>]*/>', '', x)
    x = re.sub(r'<w:(\w+PrChange|tblGridChange|numberingChange)\b[^>]*>.*?</w:\1>', '', x, flags=re.S)
    x = re.sub(r'<w:(?:moveFromRange|moveToRange)(?:Start|End)\b[^>]*/>', '', x)
    x = re.sub(r'<w:(ins|del|moveFrom|moveTo) [^>]*/>', '', x)
    x = re.sub(r'<w:(del|moveFrom) [^>]*>.*?</w:\1>', '', x, flags=re.S)
    x = re.sub(r'<w:(ins|moveTo) [^>]*>(.*?)</w:\1>', r'\2', x, flags=re.S)
    x = x.replace('<w:rPr></w:rPr>', '')
    return x


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = sys.argv[1]
    wdir = os.path.join(d, 'word')
    if not os.path.isfile(os.path.join(wdir, 'document.xml')):
        sys.exit(f'止まる：{wdir}/document.xml が無い（展開済みの .docx のフォルダを渡す）')
    out = {}
    for name in sorted(os.listdir(wdir)):
        if BODY_PART.match(name):
            p = os.path.join(wdir, name)
            with open(p, encoding='utf-8') as f:
                out[p] = accept(f.read())
    s = os.path.join(wdir, 'settings.xml')
    if os.path.exists(s):  # Word 以外のソフトで作った文書には、settings.xml が無いことがある
        with open(s, encoding='utf-8') as f:
            out[s] = f.read().replace('<w:trackRevisions/>', '')
    for p, x in out.items():  # 全部を作り直せてから書く
        with open(p, 'w', encoding='utf-8') as f:
            f.write(x)
    print('ok')


if __name__ == '__main__':
    main()
