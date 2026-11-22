"""Gmail の下書き（または送信済みのメール）の RAW を調べ、画像と添付の数を数える。送る前と送った後のゲートに使う。

使い方:
    python3 -I check_draft.py <get_draft／get_message の RAW を保存した JSON> [--expect-attachments 1] [--reply reply.txt]

- Gmail コネクタの get_draft（messageFormat=RAW）の結果は大きいので、ファイルに保存されたものを渡す。
- 調べること：
  - HTML の中の <img> の数（引用した相手のメールの署名ロゴやボタンが入っていると、送信時に添付になる）
  - 画像のパーツ（image/*）の数と、添付（attachment）の名前
  - --reply を渡すと、修正点の部分が make_reply.py の出力どおり入っているか（行頭と行末の空白は除いて比べる）
- 期待：<img> 0、画像のパーツ 0、添付は --expect-attachments の数だけ（下書きでは 0、送った後は契約書の 1）。
  どれかが違えば、終了コード 1 で止まる。
"""
import argparse
import base64
import email
import html
import json
import re
import sys
from email import policy

ap = argparse.ArgumentParser()
ap.add_argument('raw_json')
ap.add_argument('--expect-attachments', type=int, default=0)
ap.add_argument('--reply', help='make_reply.py のプレーンテキストの出力')
args = ap.parse_args()

d = json.load(open(args.raw_json, encoding='utf-8'))
raw = d['raw'] + '=' * (-len(d['raw']) % 4)
msg = email.message_from_bytes(base64.urlsafe_b64decode(raw), policy=policy.default)
parts = list(msg.walk())
htmls = [p.get_content() for p in parts if p.get_content_type() == 'text/html']
imgs = sum(len(re.findall(r'<img\b', h, flags=re.I)) for h in htmls)
image_parts = [p.get_filename() or p.get('Content-ID') or '(名前なし)' for p in parts if p.get_content_maintype() == 'image']
attachments = [p.get_filename() or '(名前なし)' for p in parts
               if p.get_content_disposition() == 'attachment' and p.get_content_maintype() != 'image']
ok = True
print(f'スレッド：{d.get("threadId")}')
print(f'HTML の <img>：{imgs}')
print(f'画像のパーツ：{len(image_parts)} {image_parts if image_parts else ""}')
print(f'添付（画像以外）：{len(attachments)} {attachments if attachments else ""}（期待 {args.expect_attachments}）')
if imgs or image_parts or len(attachments) != args.expect_attachments:
    ok = False
if args.reply:
    # 修正点の部分が、行頭と行末の空白を除いて
    # そのまま入っているか。代表が Gmail の画面で宛名などを足すのは許す（行頭の全角空白は Gmail の編集で落ちることがある）
    plain = next((p.get_content() for p in parts if p.get_content_type() == 'text/plain'), None)
    if plain is None:  # 文字だけのパートがない下書き（HTML だけ）もある。そのときは HTML から本文を取り出す
        plain = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<br\s*/?>|</div>|</p>', '\n', htmls[0] if htmls else '')))
    plain = plain.replace('\r\n', '\n')
    ref = open(args.reply, encoding='utf-8').read().split('\n')
    # make_reply.py が作る修正点の行（「・」で始まる見出しの行と「（理由）」の行）だけを取り出す
    block = [l.strip() for l in ref if l.startswith('・') or l.strip().startswith('（理由）')]
    got = [l.strip() for l in plain.split('\n') if l.strip()]
    same = any(got[i:i + len(block)] == block for i in range(len(got) - len(block) + 1))
    print(f'修正点（{len(block)} 行）が make_reply.py の出力どおり入っている：{same}')
    ok = ok and same
print('OK' if ok else 'NG：送る前に直す（引用の画像を消す、添付をそろえる）')
sys.exit(0 if ok else 1)
