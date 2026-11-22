"""changes JSON から、相手への返信メールの本文（プレーンテキストと HTML）を作る。

使い方:
    python -I make_reply.py <changes.json> --out-text reply.txt --out-html reply.html [--template template.json]

- 「主な修正点」は、changes JSON の "reply"."items" から作る。各項目は
  {"article": "第1条（目的）", "summary": "何を直したか（1行）", "reasons": ["<comments の start の段落 ID>", ...]}
  理由の文は、その段落に付けた相手向けのコメント（"comments" の "text"）を**そのまま**使う。
  だから、契約書のコメントとメール本文の理由は、一言一句同じになる。
- 前文と結びは、テンプレートの "opening"／"closing"（文字列の配列。1要素1行）で挟む。
  テンプレートは --template で渡すか、changes JSON の "reply"."template" に置く。
  宛名・署名など、相手や人の名前はテンプレート（契約ごとのデータ）にだけ書き、このコードには書かない。
- 相手に送る .docx は清書（コメントなし）なので、相手向けのコメントは、すべてメール本文の理由に入れる。
  1つでも入っていなければ止まる（照合）。
- "internal": true を付けたコメント（社内だけの「検討中」など）は、メール本文にも照合にも入れない（社内 gdoc にだけ残る。清書では消える）。
- メール本文の修正点は、この道具で作る。手で書かない。同じ JSON からは、毎回同じ出力になる。
"""
import argparse
import html
import json
import sys

ap = argparse.ArgumentParser()
ap.add_argument('changes')
ap.add_argument('--template', help='opening／closing を持つ JSON。省くと changes JSON の reply.template')
ap.add_argument('--out-text', required=True)
ap.add_argument('--out-html', required=True)
args = ap.parse_args()

spec = json.load(open(args.changes, encoding='utf-8'))
reply = spec.get('reply') or sys.exit('changes JSON に "reply" がない')
tpl = json.load(open(args.template, encoding='utf-8')) if args.template else reply.get('template')
if not tpl:
    sys.exit('テンプレートがない：--template か、changes JSON の reply.template を指定する')
comments = {}
for c in spec.get('comments', []):
    if c.get('internal'):  # 社内だけのコメント（例：「検討中」）はメール本文に入れない
        continue
    comments.setdefault(c['start'], []).append(c['text'])


def item_lines(it):
    reasons = []
    for pid in it.get('reasons', []):
        if pid not in comments:
            sys.exit(f'理由の段落 {pid} に、相手向けのコメントがない')
        reasons += comments[pid]
    return f'・{it["article"]}：{it["summary"]}', reasons


items = [item_lines(it) for it in reply['items']]

# 照合：相手向けのコメントが、メール本文の理由に漏れなく入っているか
used = {pid for it in reply['items'] for pid in it.get('reasons', [])}
missing = sorted(set(comments) - used)
if missing:
    sys.exit(f'メール本文に入っていないコメントがある（段落 {", ".join(missing)}）。reply.items の reasons に足す')


def block_text():
    out = []
    for head, reasons in items:
        out.append(head)
        for r in reasons:
            out.append(f'　（理由）{r}')
    return out


lines = list(tpl['opening']) + block_text() + list(tpl['closing'])
text = '\n'.join(lines) + '\n'
open(args.out_text, 'w', encoding='utf-8').write(text)

e = html.escape
h = ['<div>' + '<br>'.join(e(l) for l in tpl['opening']) + '</div>', '<ul>']
for head, reasons in items:
    h.append('<li>' + e(head[1:]) + ''.join(f'<br>（理由）{e(r)}' for r in reasons) + '</li>')
h.append('</ul>')
h.append('<div>' + '<br>'.join(e(l) for l in tpl['closing']) + '</div>')
open(args.out_html, 'w', encoding='utf-8').write('\n'.join(h) + '\n')
print(f'ok: items={len(items)} lines={len(lines)}')
