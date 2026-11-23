"""予算（7つ道具の「予算」）：回数・日数・お金の上限を見て、「予算切れ」で止める。

上限の数字は利用側が決める（Axla では代表が決める人間ゲート）。置き場所は利用側の `loop/legal/budget.json`。
ファイルに無い項目・値が null の項目は「上限なし」として表示し、止めない。見本は docs/budget.example.json。
既定値は、spec で決まっている「検証は1回の送付の中で5周まで」だけ。

使い方:
    python3 -I budget.py show [--root <利用側のリポジトリ>]
        上限を一覧にする（決まっていない項目は「上限なし」）。
    python3 -I budget.py cycle <契約の記録フォルダ> --version vX.Y.Z
        内側のループを1周回したときに呼ぶ。周回は「その送付の中（Y が同じ間）」で数え、Y が変わったら 1 から数え直す。
    python3 -I budget.py check <契約の記録フォルダ> [--root ...] [--review-tokens N] [--review-minutes M]
        いまの契約が上限の中かを確かめる。中なら終了コード 0、予算切れなら終了コード 3 で止まり、
        理由を「予算切れ（…）」の形で出す（Loop Log の「いまの状態」と台帳の「状態」にそのまま書ける）。

数えるもの:
    inner_cycles_per_send … 内側のループの周回（その送付の中）。gate.json の budget に道具が書く
    round_trips           … 相手との往復（台帳 register.csv の「相手との往復」）
    days_from_receipt     … 受け取ってからの日数（台帳の「受領日」から今日まで）
    review_tokens         … 1回の検証で使ったトークン（--review-tokens で渡す。司令塔がエージェントの使用量を見て渡す）
    review_minutes        … 1回の検証にかかった分（--review-minutes で渡す）
    notify_retries        … 自動検知で見張りタスクを起こすのに失敗してよい回数（Apps Script の MAX_RETRIES に同じ値を入れる）
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

LIMITS = [
    ('inner_cycles_per_send', '検証の周回（その送付の中）', '周'),
    ('round_trips', '相手との往復', '往復'),
    ('days_from_receipt', '受け取ってからの日数', '日'),
    ('review_tokens', '1回の検証のトークン', 'トークン'),
    ('review_minutes', '1回の検証の時間', '分'),
    ('notify_retries', '自動検知の再試行', '回'),
]
EXHAUSTED = 3


# 既に spec で決まっている値だけを既定にする（「5周しても致命的が 0件にならない → G1」）。
# ほかは代表が決めるまで既定値なし（上限なし）。budget.json に null と書けば、既定も外せる。
DEFAULTS = {'inner_cycles_per_send': 5}


def load_budget(root):
    lim = dict(DEFAULTS)
    p = os.path.join(root, 'loop', 'legal', 'budget.json') if root else None
    if p and os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            lim.update(json.load(f).get('limits', {}))
    return lim


def fmt(v, unit):
    return '上限なし' if v is None else f'{v} {unit}'


def register_row(root, cid):
    p = os.path.join(root, 'loop', 'legal', 'register.csv')
    if not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            if row.get('id') == cid:
                return row
    return {}


def y_of(version):
    m = re.match(r'v?(\d+)\.(\d+)\.(\d+)', version or '')
    return int(m.group(2)) if m else None


def cmd_show(root):
    lim = load_budget(root)
    for key, label, unit in LIMITS:
        print(f'{label}：{fmt(lim.get(key), unit)}')


def cmd_cycle(cdir, version):
    y = y_of(version)
    if y is None:
        sys.exit(f'版の形が違う：{version}（vX.Y.Z）')
    g = gate.load(cdir)
    b = g.get('budget', {})
    if b.get('y') != y:
        b = {'y': y, 'cycles': 0}
    b['cycles'] += 1
    b['at'] = gate.now()
    gate.update(cdir, 'budget', b)
    print(f'ok: Y={y} の送付の中で {b["cycles"]} 周目')


def cmd_check(cdir, root, tokens, minutes, today=None):
    lim = load_budget(root)
    cid = os.path.basename(os.path.normpath(cdir))
    row = register_row(root, cid) if root else {}
    used = {'inner_cycles_per_send': gate.load(cdir).get('budget', {}).get('cycles', 0)}
    if row.get('相手との往復', '').strip().isdigit():
        used['round_trips'] = int(row['相手との往復'])
    if row.get('受領日'):
        try:
            d0 = datetime.date.fromisoformat(row['受領日'].strip())
            used['days_from_receipt'] = ((today or datetime.date.today()) - d0).days
        except ValueError:
            pass
    if tokens is not None:
        used['review_tokens'] = tokens
    if minutes is not None:
        used['review_minutes'] = minutes
    over = []
    for key, label, unit in LIMITS:
        if key == 'notify_retries':
            continue  # Apps Script の中で数える
        v, u = lim.get(key), used.get(key)
        shown = '—' if u is None else f'{u} {unit}'
        mark = ''
        if v is not None and u is not None and u >= v:
            mark = '  ← 予算切れ'
            over.append(label)
        print(f'{label}：{shown} ／ {fmt(v, unit)}{mark}')
    if over:
        print('予算切れ（' + '・'.join(over) + '）')
        sys.exit(EXHAUSTED)
    print('上限の中')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('show')
    s.add_argument('--root')
    c = sub.add_parser('cycle')
    c.add_argument('cdir')
    c.add_argument('--version', required=True)
    k = sub.add_parser('check')
    k.add_argument('cdir')
    k.add_argument('--root')
    k.add_argument('--review-tokens', type=int)
    k.add_argument('--review-minutes', type=int)
    k.add_argument('--today', help='テスト用（YYYY-MM-DD）')
    a = ap.parse_args()
    if a.cmd == 'show':
        cmd_show(a.root or gate.find_root(os.getcwd()))
    elif a.cmd == 'cycle':
        cmd_cycle(a.cdir, a.version)
    else:
        root = a.root or gate.find_root(a.cdir)
        today = datetime.date.fromisoformat(a.today) if a.today else None
        cmd_check(a.cdir, root, a.review_tokens, a.review_minutes, today)


if __name__ == '__main__':
    main()
