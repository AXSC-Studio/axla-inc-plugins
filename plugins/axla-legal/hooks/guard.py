"""Axla Legal の柵（Hook）。文章の約束を、道具で止める形にする（Issue #10・#14）。

    python3 -I guard.py pre    … PreToolUse（メールの送信と下書き、LEGAL.md の書き換え、gate.json の手書き、記録の git add）
    python3 -I guard.py post   … PostToolUse（下書きを作った／変えたら、その契約の draft を「確認待ち」にする）
    python3 -I guard.py stop   … Stop（確認待ちの下書きがあれば、ターンを終わらせない）

働くのは、利用側のリポジトリに `loop/legal/` があり、契約の記録に gate.json があるときだけ。
メールの柵は、宛先・スレッド・メッセージ・下書きが、gate.json に登録した契約の相手に当たるときだけ働く。
道具やこの Hook が壊れていても、作業は止めない（止めるのは、決まりに反すると分かったときだけ）。
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import gate  # noqa: E402

MAIL = re.compile(r'^mcp__.+__(send_message|reply|forward|create_draft|update_draft)$')
SEND = {'send_message', 'reply', 'forward'}
OUTER_BRANCH = 'legal-outer/'  # 外側のループ（LEGAL.md を直す PR）のブランチの頭
FREE_MAIL = {'gmail.com', 'googlemail.com', 'yahoo.co.jp', 'yahoo.com', 'outlook.com', 'outlook.jp', 'hotmail.com',
             'icloud.com', 'me.com', 'live.jp', 'live.com', 'docomo.ne.jp', 'ezweb.ne.jp', 'softbank.ne.jp'}


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                             'permissionDecisionReason': 'Axla Legal の柵：' + reason}}, ensure_ascii=False))
    sys.exit(0)


def domain(addr):
    return addr.rsplit('@', 1)[-1].lower() if '@' in addr else ''


def project_root(data, path=None):
    for start in [path, os.environ.get('CLAUDE_PROJECT_DIR'), data.get('cwd')]:
        if start:
            r = gate.find_root(start)
            if r:
                return r
    return None


def mail_targets(inp):
    addrs = [a.lower() for k in ('to', 'cc', 'bcc') for a in (inp.get(k) or []) if isinstance(a, str)]
    ids = {k: inp.get(k) for k in ('replyThreadId', 'replyToMessageId', 'messageId', 'draftId') if inp.get(k)}
    return addrs, ids


def matches(g, addrs, ids):
    w = g.get('watch', {})
    to = set(w.get('to', []))
    doms = {domain(a) for a in to} - FREE_MAIL - {''}
    if any(a in to or domain(a) in doms for a in addrs):
        return True
    if ids.get('replyThreadId') in set(w.get('threads', [])):
        return True
    msgs = set(w.get('messages', []))
    if ids.get('replyToMessageId') in msgs or ids.get('messageId') in msgs:
        return True
    return ids.get('draftId') in set(g.get('draft', {}).get('ids', []))


def matched_contracts(root, inp):
    addrs, ids = mail_targets(inp)
    return [(cid, cdir, g) for cid, cdir, g in gate.contracts(root) if matches(g, addrs, ids)], addrs, ids


def unresolved(action, inp, addrs, ids):
    """宛先が分からない（相手かどうか判断できない）メールの操作か。"""
    if addrs:
        return False
    if action in ('reply', 'forward'):
        return True
    if action == 'create_draft' and ids.get('replyToMessageId'):
        return True
    return False


def iso_to_epoch(s):
    import datetime
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()


def check_draft_input(cid, cdir, g, inp):
    clean = g.get('clean', {})
    if not clean.get('ok'):
        deny(f'契約 {cid} の清書の検査（make_clean.py --record）が通っていない。清書を作ってから下書きにする。')
    redline = os.path.join(cdir, 'Redline Data.json')
    if os.path.exists(redline) and os.path.getmtime(redline) > iso_to_epoch(clean['at']) + 1:
        deny(f'契約 {cid} の Redline Data.json が、清書の検査のあとに変わっている。清書を作り直す（make_clean.py --record）。')
    if re.search(r'<img\b', inp.get('htmlBody') or '', flags=re.I):
        deny('下書きの HTML に画像（<img>）がある。送ると相手に意味のない添付が届く（INCIDENT の再発）。画像を外す。')
    if inp.get('attachments'):
        deny('下書きに添付を付けない。清書の添付は、代表が Gmail の画面で付ける（spec の「送信」）。')


def pre(data):
    name = data.get('tool_name', '')
    inp = data.get('tool_input') or {}
    m = MAIL.match(name)
    if m:
        action = m.group(1)
        root = project_root(data)
        if not root:
            return
        hits, addrs, ids = matched_contracts(root, inp)
        if not hits and unresolved(action, inp, addrs, ids) and any(g.get('watch') for _, _, g in gate.contracts(root)):
            deny('宛先が書かれていないので、契約の相手へのメールかどうか分からない。to を書くか、'
                 'その契約なら gate.py watch --message で登録してから、もう一度。')
        if not hits:
            return
        cids = ', '.join(c for c, _, _ in hits)
        if action in SEND:
            deny(f'契約 {cids} の相手へのメールは、AI から送らない。送信は代表が Gmail の画面で押す（人間ゲート「送信」）。')
        for cid, cdir, g in hits:
            check_draft_input(cid, cdir, g, inp)
        return

    if name in ('Edit', 'Write', 'MultiEdit', 'NotebookEdit'):
        path = inp.get('file_path') or inp.get('notebook_path') or ''
        root = project_root(data, path)
        if not root:
            return
        p = os.path.realpath(path)
        if p == os.path.realpath(os.path.join(root, 'loop', 'legal', 'LEGAL.md')) and not outer_branch(root):
            deny('LEGAL.md は中間ループの間は読むだけ。学びは Loop Log に書き、外側のループ'
                 f'（ブランチ {OUTER_BRANCH}…で PR、代表の OK）で直す。')
        if os.path.basename(p) == gate.NAME and os.sep + os.path.join('loop', 'legal', 'contracts') + os.sep in p:
            deny('gate.json は道具（make_clean.py・check_draft.py・gate.py）と Hook だけが書く。手で書き換えない。')
        return

    if name == 'Bash':
        cmd = inp.get('command') or ''
        root = project_root(data)
        if not root:
            return
        writes_legal = re.search(r'(>>?\s*\S*LEGAL\.md|\btee\b[^|;&]*LEGAL\.md|\b(sed|perl)\s+-i\S*\s[^|;&]*LEGAL\.md|'
                                 r'\b(mv|cp|rm|truncate)\b[^|;&]*LEGAL\.md|\bgit\s+(checkout|restore)\b[^|;&]*LEGAL\.md)', cmd)
        if writes_legal and not outer_branch(root):
            deny('LEGAL.md を書き換えるコマンドは止める（中間ループの間は読むだけ）。外側のループのブランチで直す。')
        if re.search(r'(>>?\s*|\btee\b[^|;&]*|\b(sed|perl)\s+-i\S*\s[^|;&]*|\b(mv|cp|rm)\b[^|;&]*)\S*contracts/[^/\s]+/gate\.json', cmd):
            deny('gate.json は道具と Hook だけが書く。手で書き換えない。')
        for seg in re.split(r'[;&|]+', cmd):
            if re.search(r'\bgit\s+add\b', seg) and (re.search(r'contracts', seg) or re.search(r'\s(-f|--force)\b', seg)):
                deny('契約の記録（loop/legal/contracts/）は git に入れない（本文と相手の名前が入るため）。git add -f も使わない。')


def outer_branch(root):
    try:
        r = subprocess.run(['git', '-C', root, 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True, timeout=5)
        return r.stdout.strip().startswith(OUTER_BRANCH)
    except (OSError, subprocess.SubprocessError):
        return False


def post(data):
    name = data.get('tool_name', '')
    m = MAIL.match(name)
    if not m or m.group(1) not in ('create_draft', 'update_draft'):
        return
    root = project_root(data)
    if not root:
        return
    inp = data.get('tool_input') or {}
    hits, _, _ = matched_contracts(root, inp)
    resp = json.dumps(data.get('tool_response'), ensure_ascii=False)
    found = re.findall(r'\\?"(id|threadId)\\?"\s*:\s*\\?"([^"\\]+)', resp)
    draft_id = next((v for k, v in found if k == 'id'), None) or inp.get('draftId')
    thread_id = next((v for k, v in found if k == 'threadId'), None)
    for cid, cdir, g in hits:
        dr = g.get('draft', {})
        ids = set(dr.get('ids', []))
        if draft_id:
            ids.add(draft_id)
        dr.update({'pending': True, 'ids': sorted(ids), 'changed_at': gate.now()})
        g['draft'] = dr
        if thread_id:
            w = g.setdefault('watch', {})
            w['threads'] = sorted(set(w.get('threads', [])) | {thread_id})
        gate.save(cdir, g)


def stop(data):
    root = project_root(data)
    if not root:
        return
    pending = [cid for cid, _, g in gate.contracts(root) if g.get('draft', {}).get('pending')]
    if not pending:
        return
    msg = ('Axla Legal の柵：契約 ' + ', '.join(pending) + ' の返信の下書きが、送る前の確認を通っていない。'
           'get_draft（RAW）を保存して `check_draft.py <file> --expect-attachments 0 --reply reply.txt --record <契約の記録フォルダ>` '
           'を走らせ、OK になってから終える。')
    if data.get('stop_hook_active'):
        print(json.dumps({'systemMessage': msg + '（同じ理由で2回止めたので、ここでは終える。代表が確かめること）'}, ensure_ascii=False))
        return
    print(json.dumps({'decision': 'block', 'reason': msg}, ensure_ascii=False))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    {'pre': pre, 'post': post, 'stop': stop}.get(mode, lambda d: None)(data)


if __name__ == '__main__':
    main()
