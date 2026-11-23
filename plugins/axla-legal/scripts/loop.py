"""入口の道具（Issue #13）：いまどの段階かを契約の記録から読み、次の1歩と、通るべき確認を決める。

使い方:
    python3 -I loop.py next <契約の記録フォルダ>            # 次の1歩を表示する
    python3 -I loop.py next <契約の記録フォルダ> --json     # 機械が読む形
    python3 -I loop.py list [--root <利用側>]               # 契約ごとの次の1歩を一覧にする

スキル `loop`（/axla-legal:loop）は、これを呼んで、表示された部品（スキル）だけを使う。
判断の材料は、契約の記録フォルダ（loop/legal/contracts/<契約 ID>/）の gate.json と Redline Data.json だけ。
道具と Hook が gate.json に書くので、手順を覚えていなくても、飛ばした確認はここで見つかる。

段階（上から順に、最初に当てはまったものが次の1歩）:
    予算切れ → G1        budget.py check が予算切れ（終了コード 3）
    intake              相手の宛先などが登録されていない（gate.json の watch が無い）
    redline-contract    Redline Data.json が無い、または検証が NG のあと
    review              最後の直しのあとに、検証が通っていない
    gdoc                最後の直しのあとに、社内 gdoc を作っていない（内側のループの最後に1回だけ作る）
    人（最終 OK）        代表が gdoc を見て「最終 OK」を出すのを待つ（gate.py mark approval）
    人（G1）            人に聞く論点がある（gate.py mark g1）。答え（gate.py mark g1_answered）が出るまで、どの段階でも止まる
    send                清書・返信文・下書き・下書きの検査のどれかが済んでいない
    人（送信）           代表が Gmail の画面で清書を添付して送るのを待つ
    INCIDENT            送ったメールの検査が NG
    相手の返事待ち        送ったメールの検査が OK
    learn               Signed・破談・INCIDENT のあと、外側のループがまだ（gate.py mark learned で閉じる）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402


def mtime(path):
    return os.path.getmtime(path) if os.path.exists(path) else None


def fresh(rec, redline_mtime):
    """記録が、最後の直し（Redline Data.json）より後のものか。"""
    return bool(rec) and rec.get('redline_mtime') is not None and redline_mtime is not None \
        and rec['redline_mtime'] >= redline_mtime - 1


def budget_exhausted(cdir):
    import subprocess
    r = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'budget.py'), 'check', cdir], capture_output=True, text=True)
    if r.returncode == 3:
        return [l for l in r.stdout.split('\n') if l.startswith('予算切れ')][-1]
    return None


def step(skill, why, then=None, human=False):
    return {'skill': skill, 'why': why, 'then': then or '', 'human': human}


def decide(cdir):
    g = gate.load(cdir)
    redline = os.path.join(cdir, 'Redline Data.json')
    rm = mtime(redline)
    if g.get('signed') or g.get('dropped') or (g.get('sent', {}).get('checked_ok') is False):
        if not g.get('learned'):
            kind = 'Signed' if g.get('signed') else '破談' if g.get('dropped') else 'INCIDENT'
            if kind == 'INCIDENT':
                return step('INCIDENT', '送ったメールの検査が NG だった（相手に余計なものが届いたかもしれない）',
                            'spec の「柵：INCIDENT → 柵を1つ足す」を 1〜5 の順に。代表に知らせる。終わったら learn へ', human=True)
            return step('learn', f'{kind}になった。学びを LEGAL.md に戻す外側のループがまだ',
                        'outer_loop.py collect → legal-outer/<契約 ID> のブランチで PR → 代表のマージ → gate.py mark learned')
        return step('done', '外側のループまで終わった')
    over = budget_exhausted(cdir)
    if over:
        return step('G1', over, '止まる。Loop Log の「いまの状態」と台帳の状態に書き、代表に知らせる', human=True)
    g1 = g.get('g1', {})
    if g1.get('open'):
        return step('人（G1）', '人に聞く論点がある：' + (g1.get('note') or '（Loop Log を見る）'),
                    '代表に論点を3行で知らせて止まる。答えが出たら gate.py mark g1_answered --note <答えの要点> で記録し、'
                    'Loop Log の「G1 の答え」に書いてから、もう一度入口へ', human=True)
    if not g.get('watch'):
        return step('intake', '相手の宛先・スレッドが登録されていない（契約の受け取りがまだ）',
                    '原本を受け取り、契約 ID と台帳の1行を作り、gate.py watch で相手を登録する')
    if rm is None:
        return step('redline-contract', 'Redline Data.json が無い（直しがまだ）', 'LEGAL.md に沿って直しを書き、redline.py → add_comments.py')
    rv = g.get('review')
    if fresh(rv, rm) and not rv.get('ok'):
        return step('redline-contract', f'検証で致命的が {rv.get("critical", "?")} 件ある', '直してから、もう一度 review')
    if not fresh(rv, rm):
        return step('review', '最後の直しのあとに、検証が通っていない',
                    'check_refs.py と検証役 → count_findings.py --record で合否を記録 → budget.py cycle')
    if not fresh(g.get('gdoc'), rm):
        return step('gdoc', '最後の直しの社内 gdoc がまだ（内側のループの最後に1回だけ作る）',
                    'つながりの create_file で .docx から gdoc を作り、古い gdoc はゴミ箱へ → gate.py mark gdoc --id <ID>')
    if not fresh(g.get('approval'), rm):
        return step('人（最終 OK）', '代表が gdoc を見て「最終 OK」か直しを出すのを待つ',
                    '代表に gdoc のリンクと「何を変えたか」を3行で知らせて止まる。OK が出たら gate.py mark approval。'
                    '直しを頼まれたら redline-contract へ', human=True)
    clean = g.get('clean', {})
    if not (clean.get('ok') and clean.get('at') and os.path.exists(redline)
            and gate_epoch(clean['at']) >= rm - 1):
        return step('send', '最終 OK のあとの清書がまだ', 'make_clean.py --record')
    if 'reply' not in g:
        return step('send', '返信文がまだ', 'make_reply.py --record')
    dr = g.get('draft', {})
    if not dr.get('ids'):
        return step('send', '返信の下書きがまだ', 'つながりの create_draft（添付なし・画像なし）')
    if dr.get('pending') or not dr.get('checked_ok'):
        return step('send', '下書きの検査が通っていない', 'get_draft を messageFormat=RAW で読む（Hook が検査する）')
    if not g.get('sent'):
        return step('人（送信）', '代表が Gmail の画面で、清書を添付して送るのを待つ',
                    '送ったら、送信済みのメールを get_message（RAW）で読む（Hook が送った後の検査をする）', human=True)
    return step('相手の返事待ち', '送ったメールの検査が OK',
                '返事が来たら、相手の版で intake からもう一度（版の Y を上げる）。署名済みなら gate.py mark signed')


def gate_epoch(s):
    import datetime
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()


def show(cid, s):
    who = '人' if s['human'] else 'Claude'
    return f'{cid}：次は「{s["skill"]}」（{who}）\n  なぜ：{s["why"]}\n  すること：{s["then"]}'


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    n = sub.add_parser('next')
    n.add_argument('cdir')
    n.add_argument('--json', action='store_true')
    ls = sub.add_parser('list')
    ls.add_argument('--root')
    a = ap.parse_args()
    if a.cmd == 'next':
        if not os.path.isdir(a.cdir):
            s = step('intake', '契約の記録フォルダがまだ無い', '原本を受け取り、契約 ID を決めて、記録フォルダと台帳の1行を作る')
        else:
            s = decide(a.cdir)
        cid = os.path.basename(os.path.normpath(a.cdir))
        print(json.dumps({'contract': cid, **s}, ensure_ascii=False) if a.json else show(cid, s))
        return
    root = a.root or gate.find_root(os.getcwd())
    if not root:
        sys.exit('止まる：loop/legal/ のあるリポジトリが見つからない。--root で渡す')
    base = os.path.join(root, 'loop', 'legal', 'contracts')
    ids = sorted(os.listdir(base)) if os.path.isdir(base) else []
    if not ids:
        print('契約の記録がまだ無い。新しい契約なら、次は「intake」')
    for cid in ids:
        if os.path.isdir(os.path.join(base, cid)):
            print(show(cid, decide(os.path.join(base, cid))))


if __name__ == '__main__':
    main()
