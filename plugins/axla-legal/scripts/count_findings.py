"""検証役の出力から、重さごとの指摘の数を道具で数え直し、合否を出す（検証役の言葉だけに頼らない）。

使い方:
    python3 -I count_findings.py <検証役の出力のファイル> [...]

- 指示文（prompts/reviewer-prompts.md 2.0.0 以降）は、指摘の行を【致命的】【重要】【軽微】で始める決まり。
  この印の数を数える。
- 出力の終わりの「致命的 N件・重要 N件・軽微 N件」（検証役が自分で数えた件数）とも比べる。
- 終了コード：0＝合格（どのファイルも致命的 0件で、件数が合う）、1＝致命的がある、2＝件数が合わない／印が無い。
  2 のときは、その検証役をもう一度回す（数を自分で直さない）。
"""
import re
import sys

LEVELS = ['致命的', '重要', '軽微']
TAG = re.compile(r'^\s*(?:[-*・]|\d+[.)．])?\s*【(致命的|重要|軽微)】', re.M)
SUMMARY = re.compile(r'致命的\s*(\d+)\s*件\s*[・、,，/／ ]\s*重要\s*(\d+)\s*件\s*[・、,，/／ ]\s*軽微\s*(\d+)\s*件')


def count(text):
    got = {k: 0 for k in LEVELS}
    for m in TAG.finditer(text):
        got[m.group(1)] += 1
    s = SUMMARY.findall(text)
    said = dict(zip(LEVELS, map(int, s[-1]))) if s else None
    return got, said


def main(paths):
    worst = 0
    total = {k: 0 for k in LEVELS}
    for p in paths:
        with open(p, encoding='utf-8') as f:
            got, said = count(f.read())
        for k in LEVELS:
            total[k] += got[k]
        line = '・'.join(f'{k} {got[k]}件' for k in LEVELS)
        if said is None:
            print(f'{p}：{line}（検証役の件数の行が無い）')
            worst = max(worst, 2)
        elif said != got:
            print(f'{p}：{line}（検証役は ' + '・'.join(f'{k} {said[k]}件' for k in LEVELS) + ' と書いた。合わない）')
            worst = max(worst, 2)
        else:
            print(f'{p}：{line}')
        if got['致命的']:
            worst = max(worst, 1)
    print('合計：' + '・'.join(f'{k} {total[k]}件' for k in LEVELS))
    if worst == 2:
        print('判定：数え直しが合わない → その検証役をもう一度回す')
    elif total['致命的']:
        print('判定：致命的あり → 直してもう1周')
    else:
        print('判定：合格（致命的 0件）')
    return worst


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
