# legal（redline-contract）：相手の雛形に、変更履歴とコメントで修正案を入れる道具

契約のループ（[specs/legal-001-run-contract-loop.md](../specs/legal-001-run-contract-loop.md)）の中間ループで、相手から届いた .docx に Axla の修正を **変更履歴（w:ins／w:del）** として入れ、修正ごとの理由を **Word のコメント** として付けるための道具です。

- 道具（このフォルダ）は汎用。**契約ごとのデータ（changes JSON・本文・相手の名前）は git に入れない**。axla-inc の `loop/legal/contracts/<契約 ID>/Redline Data.json` に置く。
- 作った .docx を Google ドキュメントに取り込むと、変更履歴は「提案」、コメントは「コメント」になる。

## 中身

| ファイル | 役割 |
|---|---|
| `redline.py` | changes JSON の `changes` を、変更履歴として `word/document.xml` に入れる |
| `add_comments.py` | changes JSON の `comments` を、Word のコメントとして入れる（本体は `comment.py`。下の「入手先」） |
| `check_draft.py` | Gmail の下書き（送った後は送信済みのメール）を調べる。HTML の `<img>`、画像のパーツ、添付の数、修正点が make_reply.py の出力どおりかを見て、違えば止まる |
| `intake_ppap.py` | パスワード付き zip（PPAP）で届いた契約書を展開する。パスワードは標準入力か入力欄で受け、表示も保存もしない（引数にしない）。中身が .docx 1つでなければ止まる |
| `make_clean.py` | 相手に送る**清書**の .docx を作る。変更をすべて反映し、コメントと作成者などの情報を消し、清書になっているかを自分で確かめてから圧縮する。通らなければ清書を作らない。**相手に送るのは清書、社内の gdoc は履歴付き** |
| `accept.py` | 変更履歴をすべて承諾した版にする（承諾後の本文の確認や、きれいな版づくりに使う） |
| `view.py` | 本文を段落ごとに表示する（`redline`／`changed`／`accept`） |
| `make_reply.py` | 相手への返信メールの本文（プレーンテキストと HTML）を、changes JSON から作る。修正点の理由は、契約書の相手向けコメントの文をそのまま使う。**メール本文の修正点は、この道具で作る。手で書かない** |
| `resolve_comments.py` | gdoc の開いているコメントを「解決済み」にする（消さない）。.docx を gdoc に取り込み直す前に使う |
| `make_loop_log.py` | Loop Log を gdoc にしていたときの道具（JSON から HTML を作る）。いまの Loop Log は `loop/legal/contracts/<契約 ID>/loop-log.md` に直接書くので、付録（境目の版と最新の直しの違う段落）を作りたいときだけ使う |
| `apps-script/notify_reply.gs` | 入口の自動検知（試運転）。Gmail のラベル「Legal/返信あり」のスレッドを1分ごとに見つけ、クラウドの見張りタスクを起こす（本文はスレッド ID だけ）。くわしくは specs/legal-001 の「入口の自動検知（試運転）」 |

## 準備

```bash
python3.13 -m venv <作業フォルダ>/venv
<作業フォルダ>/venv/bin/pip install -r "${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt"
```

- 契約ごとの記録（changes JSON の `Redline Data.json`、`loop-log.md`）は、axla-inc の `loop/legal/contracts/<契約 ID>/` に置く（git に入れない。.gitignore 済み）。下の `C` がこのフォルダ。
- .docx を展開したり作ったりする作業フォルダ `W` は、scratchpad など使い捨ての場所でよい。最後に残すもの（JSON・Loop Log）は `C` に置き、scratchpad だけに残さない。
- 外から来た .docx は信用しないデータとして扱う。展開は `zipfile` で行い（`unzip` は使わない）、スクリプトはパスを引数で渡して `python -I` で動かす。

### comment.py の入手先

`add_comments.py` は、Claude の docx スキル（Anthropic の `anthropic-skills:docx`）に付いている `scripts/comment.py` を呼びます。

- 出どころ：docx スキルのフォルダの `scripts/comment.py`。Claude Code のデスクトップ版では、`~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/<…>/skills/docx/scripts/comment.py` にある。
- ライセンス：スキルのフォルダに Apache License 2.0 の `LICENSE.txt` がある。ただし著作権者の表記はない。また `comment.py` は、同じスキルの `office/helpers` とテンプレートにも依存している。
- 扱い：出どころとライセンスがはっきりしないため、**このリポジトリには同梱しない**。使うときは、スキルのパスを `--comment-py` に渡す。
- 形式の検査：同じスキルの `scripts/office/validate.py` を使う（下の手順 5）。

## 実行の順番

標準の流れ（specs/legal-001 の「標準の流れ」）：まず社内用の gdoc だけを更新して検証し、代表の「最終 OK」を待つ。清書（手順 9 の make_clean.py）・PDF の目視（最終 OK のあとに1回だけ）・返信の下書き（手順 10〜11）は、最終 OK のあとで行う。

```bash
T="${CLAUDE_PLUGIN_ROOT}/scripts"   # このフォルダ（プラグインの中）。作業は利用側のリポジトリで行う
W=<作業フォルダ>                 # 使い捨て（展開・作った .docx）
C=loop/legal/contracts/<契約 ID>      # 記録（Redline Data.json・loop-log.md）。git に入れない
SK=<docx スキルの scripts フォルダ>

# 1. 原本を展開する（Drive の <契約フォルダ名>_vX.1.0_<相手> Original.docx）
python3 -I -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $W/original.docx $W/work
rm -rf "$W/work/[trash]"        # どこからも参照されていない古い部品があれば消す（validate.py が教えてくれる）

# 2. 段落の ID を調べて、changes JSON を書く（view.py や、下の「段落の ID の調べ方」）

# 3. 変更履歴を入れる
python3 -I $T/redline.py $W/work "$C/Redline Data.json"            # 作成者は JSON の "author"（--author で上書きできる）

# 4. コメントを入れる（comment.py が defusedxml を使うので venv の python）
$W/venv/bin/python $T/add_comments.py $W/work "$C/Redline Data.json" --comment-py $SK/comment.py   # 作成者・頭文字は JSON から。コメントの ID は既存の最大＋1 から

# 5. 再圧縮して、形式を検査する
(cd $W/work && zip -qXrDy ../redline.docx .)
$W/venv/bin/python $SK/office/validate.py $W/redline.docx --original $W/original.docx --author "Analy┊Axla Inc."

# 6. 確認する：変更のある段落と、承諾後の本文
python3 -I $T/view.py $W/work changed
python3 -I $T/view.py $W/work accept > $W/accepted.txt   # 最後に検証した直しの本文と突き合わせる

# 7. Drive の社内用の gdoc（<契約フォルダ名>_vX.Y.Z_Axla Comments）に、同じ ID のまま取り込む（新しいファイルは作らない）
#    v4 以降は、前に送った版の gdoc を vN の名前でコピーしてから取り込む（specs/legal-001 の「版の決まり」）
T_=$(gcloud auth print-access-token)   # トークンは表示しない・保存しない
#    取り込み直す前に、gdoc の開いているコメントを解決済みにする（消さない）。
#    Drive のコメントは取り込み直しても消えないので、こうしないと前のコメントと新しいコメントが二重になる
T=$T_ python3 -I $T/resolve_comments.py <その版の gdoc の ID>
curl -s -X PATCH -H "Authorization: Bearer $T_" \
  -H "Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  --data-binary @$W/redline.docx \
  "https://www.googleapis.com/upload/drive/v3/files/<その版の gdoc の ID>?uploadType=media"

# 8. Docs API で読み、提案（suggestedInsertionIds／suggestedDeletionIds）と、開いているコメントの数が changes JSON の comments の数と同じことを確かめる

# 9. specs/legal-001 の「送る前のゲート」を通す（文書のプロパティ・社内向けの混入・承諾後の本文・添付名）。
#    相手に送るのは清書。redline.docx（履歴付き）は社内用の gdoc に取り込むだけにする
#    1つのコマンドで、反映・コメント外し・情報消し・検査・圧縮までする。検査に通らなければ終了コード 1 で止まり、
#    clean.docx は残らない（前からあったものも消す）。$W/work は書き換えない。手で zip しない
python3 -I $T/make_clean.py $W/work --out $W/clean.docx --date <changes JSON の date>
#    清書を PDF に書き出して目で確かめる（下線の残り・署名欄の折れ）。通ったら、clean.docx を
#    <契約フォルダ名>_vX.Y.Z_Axla Comments.docx として契約フォルダに置く

# 10. 返信メールの本文を作る（手で書かない）。下書きは、相手のメールのスレッドの中に作り、添付は代表が付ける
python3 -I $T/make_reply.py "$C/Redline Data.json" --out-text $W/reply.txt --out-html $W/reply.html
#    下書きを作ったら、本文の修正点の部分が reply.txt と1文字も違わないことを確かめる

# 11. 送る前のゲート（下書き）：Gmail コネクタの get_draft（RAW）を保存したファイルで調べる
python3 -I $T/check_draft.py <get_draft の結果のファイル> --expect-attachments 0 --reply $W/reply.txt
#    返信の下書きには、コネクタが相手のメールを引用として足し、その中の署名ロゴやボタンの画像（<img>）も入る。
#    送ると Gmail がそれを添付に変え、相手に意味のない画像が届く。本文を差し替えても引用は付き直すので、道具では消せない。
#    → <img> や画像のパーツが残っていたら、代表に「Gmail の画面で引用部分（…）を消してから、清書を添付する」と頼む。
#    代表が添付を付けて引用を消したら、送る直前にもう一度：--expect-attachments 1（契約書の1つだけ）で OK になること

# 12. 送った後の確認：送信済みのメッセージ（get_message の RAW）を同じ道具で調べる
python3 -I $T/check_draft.py <get_message の結果のファイル> --expect-attachments 1 --reply $W/reply.txt
#    添付が契約書の1つだけ、画像のパーツ 0 であること。違えば INCIDENT として記録し、道具か手順を直す
```

- 取り込む前の版は、Drive の版の履歴に残る。戻すときは、前の版の .docx をもう一度取り込む。
- 相手に送る .docx は清書（`clean.docx`）。変更履歴とコメントはなく、何を直したか・理由はメール本文（make_reply.py）で伝える。`<契約フォルダ名>_vX.Y.Z_Axla Comments.docx` という名前で、Drive の契約フォルダに変換なしで置く（送った版の記録。N は相手との境目をまたいだ回数。specs/legal-001 の「版の決まり」）。Gmail の添付名は 120 文字までなので、長いときは役割名を短くする。

### 段落の ID の調べ方

```bash
python3 -I - "$W/work/word/document.xml" <<'EOF'
import re, sys
x = open(sys.argv[1], encoding='utf-8').read()
for p in re.findall(r'<w:p\b[^>]*?(?:/>|>.*?</w:p>)', x, flags=re.S):
    pid = re.search(r'w14:paraId="([^"]+)"', p)
    t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)<', p))
    if pid: print(pid.group(1), t[:40])
EOF
```

署名欄が表になっていることがある（左に甲・乙、右に住所と名前）。右の欄の空の段落を `insert_before` の `anchor` にする。

## changes JSON の形

```json
{
  "schema": "legal-loop/changes v1",
  "author": "Analy┊Axla Inc.",
  "initials": "AX",
  "date": "<送った版で使った日時（UTC）。例 2026-01-01T00:00:00Z>",
  "changes": [
    {"op": "rebuild",      "para": "<paraId>", "text": "<この段落の新しい本文の全体>", "clear_underline": false},
    {"op": "substitute",   "para": "<paraId>", "old": "<段落の中の語句>", "new": "<置き換える語句>"},
    {"op": "insert_after", "anchor": "<paraId>", "template": "<書式をまねる段落>", "texts": ["<足す段落>", "..."]},
    {"op": "insert_before","anchor": "<paraId>", "items": [{"template": "<paraId>", "text": "<足す段落>"}]},
    {"op": "delete",       "para": "<paraId>"}
  ],
  "comments": [
    {"start": "<paraId>", "text": "<理由。相手に見せてよい書き方で>"},
    {"start": "<paraId>", "end": "<paraId>", "text": "<複数の段落にまたがるとき>"}
  ],
  "reply": {
    "template": {"opening": ["<宛名>", "", "<あいさつ>", "…"], "closing": ["…", "<署名>"]},
    "items": [
      {"article": "<第◯条（見出し）>", "summary": "<何を直したか（1行）>", "reasons": ["<理由にするコメントの start の paraId>"]}
    ]
  }
}
```

- `rebuild` は元の本文と新しい本文の差分を文字単位で取り、変わった所だけを変更履歴にする（2文字以下の一致は、前後の変更にまとめる）。元のランの書式は保つ。
- `clear_underline: true` を付けると、その段落の残す文字と足す文字から下線を外す（雛形で空欄を示していた下線が、埋めた文字に残らないように）。外した下線は書式の変更履歴（`w:rPrChange`）として残る。
- `substitute` は、段落の中に `old` がちょうど1回あるときだけ動く。長い段落の一部を変えるときに使う。
- **制約**：`rebuild`・`substitute`・`delete` は、段落を「ランの文字」だけで組み直す。段落の中にハイパーリンク・ブックマーク・タブ・改行・フィールド・コメントの印・図・既存の変更履歴などがあると消えてしまうので、`redline.py` はその段落で止まる（エラーで終わる）。そういう段落は Word などで手で直すか、`insert_after`／`insert_before` で別の段落として足す。
- `author`／`initials` は、`--author`／`--initials` を省いたときの既定値。Axla 側の作成者名の標準は「Analy┊Axla Inc.」（区切りは全角の「┊」U+250A）。JSON にもなければ、redline.py と add_comments.py はこの名前を使う。社内 gdoc に取り込んだコメントには、名前だけが出る（顔写真は付けられない）。
- `add_comments.py` のコメントの ID は、原本にある既存のコメントの ID の最大＋1 から振る（`--comment-id-start` で指定もできる）。
- `insert_after`／`insert_before` で足した段落には、`--new-para-id-start`（既定 `1A000000`）の次の番号から順に `w14:paraId` が振られる（`1A000001`、`1A000002`、…）。コメントの `start`／`end` には、この番号を使える。
- 変更履歴の `w:id` は `--rev-id-start`（既定 9000）の次から振る。原本の既存の ID とぶつからないようにする。
- `--date` を省くと、changes JSON の `"date"`、それもなければ実行時刻（UTC）になる。送った版で使った日時を `"date"` に残しておけば、同じ JSON から毎回同じ `document.xml` ができる（再現できる）。コメントの日時と ID は `comment.py` が実行のたびに振る。

### ダミーの例（契約とは関係のない作り話）

```json
{
  "schema": "legal-loop/changes v1",
  "author": "サンプル合同会社",
  "initials": "SP",
  "changes": [
    {"op": "rebuild", "para": "0A1B2C3D", "text": "甲及び乙は、新しい焼き菓子の共同開発の可否の検討のため、本契約を締結する。"},
    {"op": "substitute", "para": "0A1B2C3E", "old": "甲の取引先", "new": "相手方の取引先"},
    {"op": "insert_after", "anchor": "0A1B2C3F", "template": "0A1B2C3F",
     "texts": ["３　持ち込んだレシピは、持ち込んだ側のものとする。"]},
    {"op": "delete", "para": "0A1B2C40"}
  ],
  "comments": [
    {"start": "0A1B2C3D", "text": "いまは試作を話し合う段階だと分かるよう、目的の書き方を変えています。"},
    {"start": "1A000001", "text": "持ち込んだレシピの扱いを、新しい項で決めています。"}
  ]
}
```

## 返信の送り方（案：スレッド外の新規の下書き。2026-11-19 に試験済み、まだ標準ではない）

スレッド内の返信の下書き（create_draft に replyToMessageId を付ける）には、次の2つの弱みがある。
- 相手のメールの引用が自動で付く。引用を外す引数はない（update_draft も同じ）。引用の中の画像は、送るときに Gmail が添付に変える（INCIDENT 2回）。
- 手元のファイル（清書）を付けるのは、アプリの決まりで止まる。代表が「ドライブから挿入」で付ける。

**試験の結果（2026-11-19）：** スレッド外の新規の下書き（replyToMessageId なし）なら、手元のファイルを付けられた。宛先は自分だけ、ダミーの .txt、送らずにすぐ消した。
- create_draft の attachments にファイル参照（`sha256:<ハッシュ>:<絶対パス>`）を渡すと、アプリの決まりで止まらずに作れた。
- check_draft.py の結果は、<img> 0・画像のパーツ 0・添付 1 で OK だった。引用も、In-Reply-To／References のヘッダーもない。
- Gmail 側では、最初から別のスレッドになる（threadId が新しい）。

**本番で使うときの注意（相手側でスレッドがつながるか）：**
- 新規の下書きには In-Reply-To／References を付けられない（コネクタに欄がない）。
- 相手側でつながるかは、件名しだいになる。そのため、件名は相手の最新のメールの件名に「RE: 」を付けたものにそろえる。
- Outlook の会話ビューは、件名（RE: などを除いた部分）が同じなら、まとめて表示することが多い。ただし、ヘッダーがないとつながらない設定や、つながらない場合もある。
- Gmail（相手が Gmail の場合）は、件名が同じでも、ヘッダーがないと別のスレッドになることがある。
- どちらも未確認なので、最初の1回は相手の画面でどう見えたかを、代表がそれとなく確かめる。

**手順の案：**
1. make_reply.py で本文を作る。
2. create_draft を次の形で呼ぶ。
   - replyToMessageId なし。
   - 宛先と CC は相手の最新のメールと同じにする。件名は「RE: <相手の最新の件名>」にする。
   - includeSignature は true。
   - attachments には清書の .docx をファイル参照で渡す。
3. get_draft（RAW）を保存し、check_draft.py --expect-attachments 1 --reply reply.txt を通す。<img> 0・画像のパーツ 0・添付 1 になるはず。
4. 代表が下書きを見て送る。送った後も check_draft.py を、送信済みメールに対して同じ条件で通す。
5. 本文の冒頭か結びに、前のやりとりを一言で書く（引用がないため）。例：「11月18日にいただいたご修正について」。

## 相手の返事を受け取る（PPAP の zip）

```bash
C=loop/legal/contracts/<契約 ID>
# 1. Gmail コネクタの download_gmail_attachment で zip を取り、受け取った名前のまま $C/received/ に置く（git に入れない）
# 2. 展開する。パスワードはメールの決まり（例：受信日の8桁）から人かループが作り、標準入力で渡す。どこにも書かない
<パスワードを出すコマンド> | python3 -I $T/intake_ppap.py "$C/received/<zip>" "$C/received"
# 3. 展開した .docx は1バイトも変えずに、Drive の契約フォルダへ <契約フォルダ名>_vX.Y.Z_<相手> Comments.docx として置く
#    （Y は境目の回数を1つ進める。Z はいまの通算のまま）。読む用の gdoc も同じ名前で作る。zip は Drive に置かない
# 4. 相手の変更履歴・コメント・文書のプロパティを確かめ（view.py changed など）、送った清書との本文の違いを取る
```

## 入口の自動検知（試運転）の設定

1. Gmail にフィルタを作る：`from:<相手のドメイン>` → ラベル「Legal/返信あり」を付ける。
2. Google Apps Script に `apps-script/notify_reply.gs` を貼る。スクリプトのプロパティに `ROUTINE_TOKEN`（claude.ai のタスク画面で発行した API の合鍵）を人が貼る。コードには書かない。
3. `install()` を1回だけ手で実行して、1分ごとのトリガーを作る。
4. 見張りタスクの道具は、Gmail の読む道具だけにする（書き込み系は `disallowed_tools` で禁止。`permitted_tools` では絞れなかった。`allowed_tools` に無い Bash も動いたので、禁止は明示する）。
5. 大きいスレッドは get_thread が溢れるので、search と get_message で読む。返事が別スレッドで来ることもある。

## 再現テスト（道具を直したら必ず）

1件目の送付版で確かめた手順。Drive の `_vX.1.0_<相手> Original.docx` と `loop/legal/contracts/<契約 ID>/Redline Data.json` から作り直し、送った `_vX.Y.Z_Axla Comments.docx` と比べる。

- `word/document.xml`：同じ `--date` なら、バイト単位で一致する（2026-11-16 に確認）。
- `word/comments.xml`：`w:date` と、`comment.py` が乱数で振る `w14:paraId`／`w14:textId` を除けば一致する。
- `make_reply.py`：同じ JSON から2回作り、プレーンテキストと HTML が1文字も違わないこと。相手向けのコメントが、すべてメール本文に入っていること（入っていなければ止まる）。
- 清書（`make_clean.py`）：同じ JSON と `--date` から2回作り、すべての部品がバイト単位で同じこと。変更履歴・コメントが 0 であること。
- 自動テスト：`python3 -I -m unittest discover -s "$T/tests"`（作り話の契約書で、清書が通る例と止まる例を確かめる）。
- 違ってよいのは、コメントの4つの部品（`comments.xml`・`commentsExtended.xml`・`commentsExtensible.xml`・`commentsIds.xml`）の日時と乱数の ID だけ。
