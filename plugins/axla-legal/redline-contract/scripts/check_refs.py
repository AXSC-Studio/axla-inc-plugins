"""条・項の参照を機械で確かめる（Issue #35）。参照の誤りは、どれも【致命的】として出す。

使い方:
    python3 -I check_refs.py <展開済みの .docx のフォルダ> [--out <file>]

- 変更をすべて承諾したあとの本文で調べる（元のフォルダは書き換えない）。
- 条：「第N条」または「第N条（見出し）」だけの段落を、条の見出しとみなす。
- 項と号：条の見出しのあとの段落のうち、Word の自動の番号の深さ（ilvl）が 0 か番号の無いものを項、1 以上を号とみなす。
- 確かめること：
  1. 「第N条」の参照先の条があるか
  2. 「第N条第M項」の項の数が足りているか
  3. 第1条の中の「前条」、条の最初の項の中の「前項」（指す先が無い）
- 出力は検証役と同じ形（【致命的】で始まる行と、最後の件数の行）。count_findings.py にそのまま渡せる。
- 終了コード：0＝参照の誤り 0件、1＝誤りがある。
- 意味の取り違え（正しく書けているが、指したい条と違う）は見つけられない。それは検証役が見る。
"""
import argparse
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from accept import accept  # noqa: E402

KANJI = {'〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
NUM = r'[0-9０-９一二三四五六七八九十百]+'


def to_int(s):
    s = s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    if s.isdigit():
        return int(s)
    n, cur = 0, 0
    for c in s:
        if c == '百':
            n += (cur or 1) * 100
            cur = 0
        elif c == '十':
            n += (cur or 1) * 10
            cur = 0
        else:
            cur = KANJI[c]
    return n + cur


def paragraphs(x):
    body = x[x.find('<w:body>'):]
    out = []
    for p in re.findall(r'<w:p\b(?:(?!<w:p\b).)*?</w:p>', body, flags=re.S):
        text = html.unescape(''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', p))).strip()
        if not text:
            continue
        m = re.search(r'<w:numPr>.*?<w:ilvl w:val="(\d+)"/>', p, flags=re.S)
        has_num = '<w:numPr>' in p
        out.append((text, int(m.group(1)) if m else (0 if has_num else None)))
    return out


def structure(paras):
    """[(条の番号, [項の段落の文字...], [(項の番号, 段落の文字)...])] を返す。"""
    arts = []
    for text, ilvl in paras:
        # 見出しは「第N条」だけか「第N条（見出し）」の形（本文が「第1条から…」で始まる段落を見出しにしない）
        m = re.match(r'^第(%s)条(?:\s*[（(][^）)]*[）)])?\s*$' % NUM, text)
        if m:
            arts.append({'n': to_int(m.group(1)), 'head': text, 'paras': []})
            continue
        if not arts:
            continue
        a = arts[-1]
        if ilvl is None or ilvl == 0:
            a['paras'].append({'text': text, 'items': []})
        elif a['paras']:
            a['paras'][-1]['items'].append(text)
        else:
            a['paras'].append({'text': text, 'items': []})
    return arts


def check(arts):
    found = []
    nums = {a['n']: a for a in arts}
    for a in arts:
        units = [(0, a['head'])] + [(i + 1, p['text']) for i, p in enumerate(a['paras'])] + \
                [(i + 1, t) for i, p in enumerate(a['paras']) for t in p['items']]
        for k, text in units:
            where = f'第{a["n"]}条' + (f'第{k}項' if k else '（見出し）')
            for m in re.finditer(r'第(%s)条(?:第(%s)項)?' % (NUM, NUM), text):
                n = to_int(m.group(1))
                if n not in nums:
                    found.append(f'{where}：「{m.group(0)}」の第{n}条が無い')
                elif m.group(2):
                    j = to_int(m.group(2))
                    have = max(len(nums[n]['paras']), 1)
                    if j > have:
                        found.append(f'{where}：「{m.group(0)}」の第{n}条は{have}項までしか無い')
            if '前条' in text and a['n'] == min(nums):
                found.append(f'{where}：最初の条の中で「前条」を指している（前の条が無い）')
            if '前項' in text and k == 1:
                found.append(f'{where}：条の最初の項の中で「前項」を指している（前の項が無い）')
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('unpacked')
    ap.add_argument('--out')
    args = ap.parse_args()
    src = os.path.join(args.unpacked, 'word', 'document.xml')
    if not os.path.isfile(src):
        sys.exit(f'止まる：{src} が無い')
    with open(src, encoding='utf-8') as f:
        x = accept(f.read())
    arts = structure(paragraphs(x))
    if not arts:
        sys.exit('止まる：「第N条」で始まる条の見出しが見つからない。この道具では確かめられない（人か検証役が見る）')
    found = check(arts)
    lines = [f'- 【致命的】{s}。直し方：参照先の条・項を正しく書き直す' for s in found]
    lines.append(f'\n致命的 {len(found)}件・重要 0件・軽微 0件')
    text = '\n'.join(lines) + '\n'
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(text)
    print(f'条 {len(arts)}・項 {sum(len(a["paras"]) for a in arts)} を調べた')
    print(text, end='')
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
