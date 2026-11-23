"""外側のループ（5 → 1）：契約で覚えたことを、次の定義（LEGAL.md と指示文）に戻す。

きっかけは3つ：Signed・破談・INCIDENT。手順は specs/legal-001 の「外側のループ」。

使い方:
    python3 -I outer_loop.py collect [--root <利用側>] [--contract <契約 ID> ...] [--out <file>]
        契約の Loop Log（loop/legal/contracts/<契約 ID>/loop-log.md）から「学び」の節を集め、
        LEGAL.md を直す PR の下書きの材料にする。集めた文は契約の記録から来るので、相手の社名・人名・
        条文が混ざりうる。PR に書く前に、相手が分からない書き方に直す（git に入れない決まり）。
    python3 -I outer_loop.py bump [--root <利用側>]
        LEGAL.md の世代（`世代：**N**`）を N+1 にする。ブランチ名が `legal-outer/` で始まるときだけ動く
        （中間ループの間に LEGAL.md を書き換えない柵。hooks/guard.py と同じ決まり）。
        代表の OK（PR のマージ）の前の、PR の中で使う。
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

OUTER_BRANCH = 'legal-outer/'
GEN = re.compile(r'(世代：\*\*)(\d+)(\*\*)')


def learnings(text):
    """Markdown の中の、見出しに「学び」を含む節の本文を返す（次の同じか上の見出しまで）。"""
    lines = text.split('\n')
    out, level = [], None
    for line in lines:
        m = re.match(r'^(#+)\s+(.*)', line)
        if m:
            if level is not None and len(m.group(1)) <= level:
                level = None
            if level is None and '学び' in m.group(2):
                level = len(m.group(1))
                continue
        if level is not None:
            out.append(line)
    return '\n'.join(out).strip()


def branch(root):
    r = subprocess.run(['git', '-C', root, 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True)
    return r.stdout.strip()


def cmd_collect(root, ids, out):
    base = os.path.join(root, 'loop', 'legal', 'contracts')
    ids = ids or (sorted(os.listdir(base)) if os.path.isdir(base) else [])
    parts = []
    for cid in ids:
        p = os.path.join(base, cid, 'loop-log.md')
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8') as f:
            body = learnings(f.read())
        if body:
            parts.append(f'## {cid}\n\n{body}\n')
    text = ('# 外側のループの材料（git に入れない。相手の社名・人名・条文を消してから PR に書く）\n\n'
            + ('\n'.join(parts) if parts else '（「学び」の節のある Loop Log が無い）\n'))
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'ok: {len(parts)} 件の契約から集めた → {out}')
    else:
        print(text)


def cmd_bump(root):
    b = branch(root)
    if not b.startswith(OUTER_BRANCH):
        sys.exit(f'止めた：ブランチ「{b}」は外側のループのブランチ（{OUTER_BRANCH}…）ではない。LEGAL.md の世代は上げない。')
    p = os.path.join(root, 'loop', 'legal', 'LEGAL.md')
    with open(p, encoding='utf-8') as f:
        t = f.read()
    m = GEN.search(t)
    if not m:
        sys.exit('止めた：LEGAL.md に「世代：**N**」が見つからない。')
    n = int(m.group(2)) + 1
    t = t[:m.start()] + f'{m.group(1)}{n}{m.group(3)}' + t[m.end():]
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t)
    print(f'ok: LEGAL.md の世代を {n - 1} → {n} にした。変更履歴に「世代 {n}」の行を足し、PR で代表の OK をもらう。')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('collect')
    c.add_argument('--root')
    c.add_argument('--contract', action='append', default=[])
    c.add_argument('--out')
    b = sub.add_parser('bump')
    b.add_argument('--root')
    a = ap.parse_args()
    root = a.root or gate.find_root(os.getcwd())
    if not root:
        sys.exit('止めた：loop/legal/ のあるリポジトリが見つからない。--root で渡す。')
    if a.cmd == 'collect':
        cmd_collect(root, a.contract, a.out)
    else:
        cmd_bump(root)


if __name__ == '__main__':
    main()
