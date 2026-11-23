"""検証役の出力から、重さごとの指摘の数を道具で数え直し、合否を出す（検証役の言葉だけに頼らない）。

使い方:
    python3 -I count_findings.py <検証役の出力のファイル> [...]

- 指示文（prompts/reviewer-prompts.md 2.0.0 以降）は、指摘の行を【致命的】【重要】【軽微】で始める決まり。
  この印の数を数える。
- 出力の終わりの「致命的 N件・重要 N件・軽微 N件」（検証役が自分で数えた件数）とも比べる。
- 重さは道具で決め直す：【重要】【軽微】でも、条・項の参照の誤り（参照・前条・前項・第N条第M項 と、誤り・違い・ずれ・無い）の
  指摘は、決まりどおり致命的として数える（検証役が重さを軽く付けても、合格の線を甘くしない。Issue #35）。
  そのときは、検証役が書いた件数とは比べずに、決め直した数で判定する。
- check_refs.py の出力も、同じ形なので一緒に渡せる。
- 終了コード：0＝合格（どのファイルも致命的 0件で、件数が合う）、1＝致命的がある、2＝件数が合わない／印が無い。
  2 のときは、その検証役をもう一度回す（数を自分で直さない）。
"""
import re
import sys

LEVELS = ['致命的', '重要', '軽微']
TAG = re.compile(r'^\s*(?:[-*・]|\d+[.)．])?\s*【(致命的|重要|軽微)】(.*)$', re.M)
REF = re.compile(r'(参照|前条|前項|同条|同項|第[0-9０-９一二三四五六七八九十]+条第[0-9０-９一二三四五六七八九十]+項)')
WRONG = re.compile(r'(誤|違|ずれ|存在しない|無い|ない|不整合|食い違)')
SUMMARY = re.compile(r'致命的\s*(\d+)\s*件\s*[・、,，/／ ]\s*重要\s*(\d+)\s*件\s*[・、,，/／ ]\s*軽微\s*(\d+)\s*件')


def count(text):
    """(印どおりの数, 検証役が書いた数, 重さを決め直した数, 決め直した行) を返す。"""
    got = {k: 0 for k in LEVELS}
    fixed = {k: 0 for k in LEVELS}
    raised = []
    for m in TAG.finditer(text):
        level, body = m.group(1), m.group(2)
        got[level] += 1
        if level != '致命的' and REF.search(body) and WRONG.search(body):
            fixed['致命的'] += 1
            raised.append(body.strip()[:80])
        else:
            fixed[level] += 1
    s = SUMMARY.findall(text)
    said = dict(zip(LEVELS, map(int, s[-1]))) if s else None
    return got, said, fixed, raised


def main(paths):
    worst = 0
    total = {k: 0 for k in LEVELS}
    for p in paths:
        with open(p, encoding='utf-8') as f:
            got, said, fixed, raised = count(f.read())
        for r in raised:
            print(f'{p}：参照の誤りは致命的として数える ← 「{r}」')
        for k in LEVELS:
            total[k] += fixed[k]
        line = '・'.join(f'{k} {got[k]}件' for k in LEVELS)
        if said is None:
            print(f'{p}：{line}（検証役の件数の行が無い）')
            worst = max(worst, 2)
        elif said != got:
            print(f'{p}：{line}（検証役は ' + '・'.join(f'{k} {said[k]}件' for k in LEVELS) + ' と書いた。合わない）')
            worst = max(worst, 2)
        else:
            print(f'{p}：{line}')
        if fixed['致命的']:
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
