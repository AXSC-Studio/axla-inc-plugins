"""gdoc の開いているコメントを「解決済み」にする（消さない）。.docx を gdoc に取り込み直す前に使う。

.docx を同じ gdoc に取り込み直すと、本文は置き換わるが、Drive のコメントは消えずに残る。
そのままだと、前のコメントと新しいコメントが二重になる。取り込む前に、開いているコメントを解決済みにしておく。

使い方:
    GOOGLE_ACCESS_TOKEN=$(gcloud auth print-access-token) python3 -I resolve_comments.py <gdoc の ID> [--before 2026-01-01T00:00:00Z] [--dry-run]

- 環境変数 GOOGLE_ACCESS_TOKEN のアクセストークンを使う（トークンは表示しない・保存しない。コマンドの引数にも入れない）。
  道具のフォルダの T とは別の名前にしてある。
- 標準の流れでは使わない（gdoc は内側のループの最後に1回だけ作るため）。前からある gdoc を直すときだけ。
- --before を付けると、その時刻より前に作られたコメントだけを解決済みにする。
- 解決済みにするには、"resolve" の返信を1つ付ける（Drive API の replies.create）。コメントは消さない。
- 最後に、開いているコメントと解決済みのコメントの数を表示する。
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument('file_id')
ap.add_argument('--before', help='この時刻（RFC 3339）より前に作られたコメントだけ')
ap.add_argument('--note', default='取り込み直しの前に、解決済みにしました。', help='解決の返信に書く文（社内用）')
ap.add_argument('--dry-run', action='store_true')
args = ap.parse_args()
TOKEN = os.environ.get('GOOGLE_ACCESS_TOKEN') or sys.exit('環境変数 GOOGLE_ACCESS_TOKEN にアクセストークンを入れる')
TIMEOUT = 30  # 秒。応答が無いまま止まり続けないように
BASE = f'https://www.googleapis.com/drive/v3/files/{args.file_id}/comments'


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)


def all_comments():
    out, token = [], None
    while True:
        q = {'fields': 'nextPageToken,comments(id,createdTime,resolved,deleted)', 'pageSize': 100}
        if token:
            q['pageToken'] = token
        r = call('GET', BASE + '?' + urllib.parse.urlencode(q))
        out += [c for c in r.get('comments', []) if not c.get('deleted')]
        token = r.get('nextPageToken')
        if not token:
            return out


targets = [c for c in all_comments() if not c.get('resolved') and (not args.before or c['createdTime'] < args.before)]
print(f'解決済みにする：{len(targets)} 件' + ('（dry run）' if args.dry_run else ''))
if not args.dry_run:
    for c in targets:
        call('POST', f'{BASE}/{c["id"]}/replies?fields=id,action', {'action': 'resolve', 'content': args.note})
cs = all_comments()
print(f'開いている：{sum(1 for c in cs if not c.get("resolved"))} 件／解決済み：{sum(1 for c in cs if c.get("resolved"))} 件')
