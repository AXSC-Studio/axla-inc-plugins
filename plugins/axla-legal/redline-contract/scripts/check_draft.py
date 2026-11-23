"""Gmail の下書き（または送信済みのメール）の RAW を調べ、画像と添付の数を数える。送る前と送った後のゲートに使う。

ふだんは手で走らせなくてよい：Gmail のつながりの get_draft／get_message を messageFormat=RAW で呼ぶと、
Hook（hooks/guard.py の post）がその結果をこの検査にかけ、gate.json に記録する（Issue #34）。

手で走らせるとき:
    python3 -I check_draft.py <get_draft／get_message の結果を保存した JSON> [--expect-attachments 1] [--reply reply.txt] [--record <契約の記録フォルダ>]

- JSON は、つながりの結果そのままでよい（どこかに "raw" があれば見つける）。
- 調べること：
  - HTML の中の <img> の数（引用した相手のメールの署名ロゴやボタンが入っていると、送信時に添付になる）
  - 画像のパーツ（image/*）の数と、添付（attachment）の名前
  - --reply を渡すと、修正点の部分が make_reply.py の出力どおり入っているか（行頭と行末の空白は除いて比べる）。
    修正点の行が reply.txt に1行も無いとき、下書きの「・」の行の数が reply.txt と違うときも止まる（Issue #20）。
- 期待：<img> 0、画像のパーツ 0、添付は --expect-attachments の数だけ（下書きでは 0、送った後は契約書の 1）。
  どれかが違えば、終了コード 1 で止まる。
- --record を渡すと、契約の gate.json の draft に結果を書く。下書きを作った／変えたあと、
  ここで OK が記録されるまで、Hook（Stop）はターンを終わらせない。
"""
import argparse
import base64
import email
import html
import json
import os
import re
import sys
from email import policy


def find_raw(obj):
    """つながりの結果（入れ子の JSON・JSON 文字列・content の配列）から、(raw, threadId, id) を探す。"""
    if isinstance(obj, str):
        s = obj.strip()
        if s.startswith('{') or s.startswith('['):
            try:
                return find_raw(json.loads(s))
            except ValueError:
                return None
        return None
    if isinstance(obj, dict):
        if isinstance(obj.get('raw'), str):
            return obj['raw'], obj.get('threadId'), obj.get('id')
        for v in obj.values():
            r = find_raw(v)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = find_raw(v)
            if r:
                return r
    return None


def check(raw, expect_attachments=0, reply_text=None):
    """(合否, 表示の行のリスト) を返す。"""
    raw = raw + '=' * (-len(raw) % 4)
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw), policy=policy.default)
    parts = list(msg.walk())
    htmls = [p.get_content() for p in parts if p.get_content_type() == 'text/html']
    imgs = sum(len(re.findall(r'<img\b', h, flags=re.I)) for h in htmls)
    image_parts = [p.get_filename() or p.get('Content-ID') or '(名前なし)' for p in parts if p.get_content_maintype() == 'image']
    attachments = [p.get_filename() or '(名前なし)' for p in parts
                   if p.get_content_disposition() == 'attachment' and p.get_content_maintype() != 'image']
    out = [f'HTML の <img>：{imgs}',
           f'画像のパーツ：{len(image_parts)} {image_parts if image_parts else ""}',
           f'添付（画像以外）：{len(attachments)} {attachments if attachments else ""}（期待 {expect_attachments}）']
    ok = not (imgs or image_parts or len(attachments) != expect_attachments)
    if reply_text is not None:
        # 修正点の部分が、行頭と行末の空白を除いてそのまま入っているか。代表が Gmail の画面で宛名などを足すのは許す
        # （行頭の全角空白は Gmail の編集で落ちることがある）
        plain = next((p.get_content() for p in parts if p.get_content_type() == 'text/plain'), None)
        if plain is None:  # 文字だけのパートがない下書き（HTML だけ）もある。そのときは HTML から本文を取り出す
            plain = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<br\s*/?>|</div>|</p>', '\n', htmls[0] if htmls else '')))
        plain = plain.replace('\r\n', '\n')
        ref = reply_text.replace('\r\n', '\n').split('\n')
        # make_reply.py が作る修正点の行（「・」で始まる見出しの行と「（理由）」の行）だけを取り出す
        block = [l.strip() for l in ref if l.startswith('・') or l.strip().startswith('（理由）')]
        got = [l.strip() for l in plain.split('\n') if l.strip()]
        if not block:
            out.append('修正点：reply.txt に修正点の行（「・」と「（理由）」）が1行も無い。make_reply.py の出力を渡す')
            ok = False
        else:
            same = any(got[i:i + len(block)] == block for i in range(len(got) - len(block) + 1))
            n_ref = sum(1 for l in block if l.startswith('・'))
            n_got = sum(1 for l in got if l.startswith('・'))
            out.append(f'修正点（{len(block)} 行）が make_reply.py の出力どおり入っている：{same}')
            out.append(f'「・」の行の数：下書き {n_got}／reply.txt {n_ref}')
            ok = ok and same and n_got == n_ref
    return ok, out


def record(cdir, ok, expect_attachments, kind='draft'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gate
    g = gate.load(cdir)
    dr = g.get(kind, {})
    dr.update({'checked_ok': ok, 'checked_at': gate.now(), 'expect_attachments': expect_attachments})
    if ok:
        dr['pending'] = False
    gate.update(cdir, kind, dr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('raw_json')
    ap.add_argument('--expect-attachments', type=int, default=0)
    ap.add_argument('--reply', help='make_reply.py のプレーンテキストの出力')
    ap.add_argument('--record', help='契約の記録フォルダ（loop/legal/contracts/<契約 ID>）。gate.json に結果を書く')
    args = ap.parse_args()
    with open(args.raw_json, encoding='utf-8') as f:
        found = find_raw(json.load(f))
    if not found:
        sys.exit('JSON に "raw" が無い。get_draft／get_message を messageFormat=RAW で呼んだ結果を渡す')
    raw, thread, _ = found
    reply_text = None
    if args.reply:
        with open(args.reply, encoding='utf-8') as f:
            reply_text = f.read()
    ok, lines = check(raw, args.expect_attachments, reply_text)
    print(f'スレッド：{thread}')
    print('\n'.join(lines))
    if args.record:
        record(args.record, ok, args.expect_attachments)
    print('OK' if ok else 'NG：送る前に直す（引用の画像を消す、添付をそろえる）')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
