"""契約ごとの「ゲートの記録」（gate.json）を読み書きする。Hook（hooks/guard.py）と道具が使う。

gate.json は利用側の `loop/legal/contracts/<契約 ID>/gate.json` に置く（契約の記録と同じ所。git に入れない）。
相手のメールアドレスが入るので、プラグインのフォルダにも git にも置かない。

使い方:
    python3 -I gate.py watch <契約の記録フォルダ> --to <相手のアドレス> [--to ...] [--thread <threadId>] [--message <messageId>]
        相手の宛先・スレッド・メッセージを登録する（入口で1回。返事が別スレッドで来たら足す）。
    python3 -I gate.py status <契約の記録フォルダ>
        ゲートの記録を表示する。
    python3 -I gate.py mark <契約の記録フォルダ> <approval|gdoc|signed|dropped|learned|g1|g1_answered> [--id <gdoc の ID>] [--note ...]
        g1 は人に聞く論点があるとき（答えが出るまで入口が止まる）、g1_answered は代表が答えたとき。
        段階が済んだことを記録する（loop.py が次の1歩を決めるのに使う）。approval（代表の最終 OK）・signed・dropped は
        人間ゲートなので、代表がチャットで言ったときだけ付ける。gdoc は社内 gdoc を作ったとき（--id にその ID）。
        approval と gdoc には、そのときの Redline Data.json の時刻を一緒に残す（あとで直しが変われば、やり直しになる）。

道具が書く項目:
    clean  … make_clean.py --record が書く（清書の検査に通った・清書の sha256・時刻）
    draft  … Hook が下書きを作った／変えたときに pending にし、check_draft.py --record が通ったら checked にする
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

NAME = 'gate.json'


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load(cdir):
    p = os.path.join(cdir, NAME)
    if not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def ensure_ignored(cdir):
    """契約の記録フォルダが git の除外に入っているかを確かめ、入っていなければ止まる（#22）。
    このリポジトリの .gitignore は、使う側のリポジトリには効かない。使う側で除外を忘れると、
    契約の本文や相手の名前がそのままコミットされる。git の外なら確かめない。"""
    d = os.path.abspath(cdir)
    probe = os.path.join(d, '_probe_gitignore')
    r = subprocess.run(['git', '-C', os.path.dirname(d) if not os.path.isdir(d) else d, 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return
    top = r.stdout.strip()
    c = subprocess.run(['git', '-C', top, 'check-ignore', '-q', probe], capture_output=True)
    if c.returncode != 0:
        sys.exit('止まる：契約の記録フォルダ（loop/legal/contracts/）が git の除外に入っていない。'
                 '使う側のリポジトリの .gitignore に `loop/legal/contracts/` の1行を足してから、もう一度。'
                 '（契約の本文や相手の名前がコミットされるのを防ぐため）')


def save(cdir, g):
    os.makedirs(cdir, exist_ok=True)
    ensure_ignored(cdir)
    p = os.path.join(cdir, NAME)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(tmp, p)


def update(cdir, key, value):
    g = load(cdir)
    g[key] = value
    save(cdir, g)
    return g


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def find_root(start):
    """start から上にたどって、`loop/legal/` のあるフォルダ（利用側のリポジトリ）を返す。無ければ None。"""
    d = os.path.abspath(start)
    if os.path.isfile(d):
        d = os.path.dirname(d)
    while True:
        if os.path.isdir(os.path.join(d, 'loop', 'legal')):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


CONFIG_KEYS = ('our_party_name', 'author', 'initials', 'doc_label', 'ai_usage', 'our_registered_address', 'our_representative')


def load_config(start):
    """利用側の loop/legal/config.json（自社名・作成者名など）を読む。見つからなければ空の辞書。
    値が「<」で始まる（ひな形のまま）項目は、無いものとして扱う。"""
    root = find_root(start) if start else None
    p = os.path.join(root, 'loop', 'legal', 'config.json') if root else None
    if not p or not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8') as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if k in CONFIG_KEYS and isinstance(v, str) and v and not v.startswith('<')}


def contracts(root):
    """(契約 ID, 記録フォルダ, gate.json の中身) を、gate.json のある契約だけ返す。"""
    base = os.path.join(root, 'loop', 'legal', 'contracts')
    out = []
    if not os.path.isdir(base):
        return out
    for cid in sorted(os.listdir(base)):
        cdir = os.path.join(base, cid)
        if os.path.isfile(os.path.join(cdir, NAME)):
            try:
                out.append((cid, cdir, load(cdir)))
            except (OSError, ValueError):
                out.append((cid, cdir, {'broken': True}))
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    w = sub.add_parser('watch')
    w.add_argument('cdir')
    w.add_argument('--to', action='append', default=[])
    w.add_argument('--thread', action='append', default=[])
    w.add_argument('--message', action='append', default=[])
    s = sub.add_parser('status')
    s.add_argument('cdir')
    mk = sub.add_parser('mark')
    mk.add_argument('cdir')
    mk.add_argument('what', choices=['approval', 'gdoc', 'signed', 'dropped', 'learned', 'g1', 'g1_answered'])
    mk.add_argument('--id')
    mk.add_argument('--note')
    args = ap.parse_args()
    if args.cmd == 'mark':
        rec = {'at': now()}
        redline = os.path.join(args.cdir, 'Redline Data.json')
        if os.path.exists(redline):
            rec['redline_mtime'] = os.path.getmtime(redline)
        if args.id:
            rec['id'] = args.id
        if args.note:
            rec['note'] = args.note
        if args.what == 'gdoc' and not args.id:
            sys.exit('gdoc には --id（作った gdoc の ID）が要る')
        if args.what == 'g1':  # 人に聞く論点がある（答えが出るまで、入口は止まる）
            rec['open'] = True
            update(args.cdir, 'g1', rec)
        elif args.what == 'g1_answered':  # 代表が答えた（--note に答えの要点。相手の名前・条文は書かない）
            g = load(args.cdir).get('g1', {})
            g.update({'open': False, 'answered_at': rec['at'], 'answer': args.note or ''})
            update(args.cdir, 'g1', g)
        else:
            update(args.cdir, args.what, rec)
        print(f'ok: {args.what} を記録した')
        return
    if args.cmd == 'watch':
        g = load(args.cdir)
        watch = g.setdefault('watch', {'to': [], 'threads': [], 'messages': []})
        for key, vals in [('to', [v.lower() for v in args.to]), ('threads', args.thread), ('messages', args.message)]:
            watch[key] = sorted(set(watch.get(key, [])) | set(vals))
        save(args.cdir, g)
        print(f'ok: 宛先 {len(watch["to"])}・スレッド {len(watch["threads"])}・メッセージ {len(watch["messages"])} を見張る')
    else:
        json.dump(load(args.cdir), sys.stdout, ensure_ascii=False, indent=2)
        print()


if __name__ == '__main__':
    main()
