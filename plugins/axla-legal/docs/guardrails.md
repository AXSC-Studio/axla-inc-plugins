# 柵（Hook）：文章の約束を、道具で止める

ループの基本形（定義 → 回す → 確かめる → 覚える → 柵）の「柵」。送る前のゲートと閉じた世界を、手順書の約束ではなく、Claude Code の Hook で止めます（[hooks/hooks.json](../hooks/hooks.json)、本体は [hooks/guard.py](../hooks/guard.py)）。プラグインを入れると、Hook も一緒に入ります。

## 何を止めるか

| いつ | 止めること | 理由 |
|---|---|---|
| メールを送る（send_message・reply・forward） | 契約の相手への送信は、いつも止める | 送信は代表が Gmail の画面で押す（人間ゲート「送信」） |
| 下書きを作る・変える（create_draft・update_draft） | 清書の検査（`make_clean.py --record`）が通っていない／その後に `Redline Data.json` が変わった／HTML に `<img>` がある／添付がある | 送る前のゲートを飛ばさない。画像入りの下書きは INCIDENT を2回起こした |
| 下書きを作った・変えたあと、ターンを終える（Stop） | 下書きの検査が OK になるまで、終わらせない（同じ理由で2回目は終えて、代表に知らせる） | 引用に付いてくる画像は、下書きを読み直さないと分からない |
| 下書きや送ったメールを読む（get_draft・get_message を messageFormat=RAW で） | その場で検査し（画像・添付・修正点が reply.txt どおりか、修正点が0行でないか）、gate.json に書き、結果を Claude に返す。送ったメールが NG なら INCIDENT と知らせる | 検査を「人が走らせる手順」にしない（#34） |
| 宛先の無い reply・forward、登録の無いメッセージへの返信の下書き | 契約の相手かどうか分からないので止める（`to` を書くか、登録してから） | 抜け道をふさぐ |
| `loop/legal/LEGAL.md` を書き換える（Edit・Write・Bash のリダイレクトや `sed -i` など） | ブランチ名が `legal-outer/` で始まらなければ止める | 中間ループの間は読むだけ。学びは Loop Log に書き、外側のループで直す |
| `gate.json` を手で書く | いつも止める | ゲートの記録は、道具と Hook だけが書く |
| `git add` で `loop/legal/contracts/` や契約書のファイル（.docx・.zip、`loop/legal/` の下の .pdf、`Redline Data.json`）を入れる、`git add -f` | いつも止める | 契約の本文・相手の名前を git に入れない |
| `git commit`・`git push` で、ステージ（push なら上流に無いコミット）に契約書や契約の記録らしいファイルがある | 止める（`git add -A` で入ってしまった形も） | 同上 |
| 契約の記録を書く道具（gate.py を使うもの）を、`loop/legal/contracts/` が git の除外に入っていないリポジトリで使う | 書く前に止める（.gitignore に1行足すよう知らせる） | このプラグインの .gitignore は、使う側のリポジトリには効かない |

- 働くのは、いま開いているリポジトリに `loop/legal/` があるときだけ。メールの柵は、`gate.json` に登録した相手（アドレス・同じドメイン・スレッド・メッセージ・作った下書き）に当たるときだけ働きます。ほかのメールは止めません（フリーメールのドメインは、ドメインでは当てません）。
- Hook は「うっかり」と「手順の飛ばし」を止める柵です。わざと回り道をすれば抜けられます（たとえば別の言語のスクリプトで書き換える）。だから、送信・署名は人だけが押す、という人間ゲートは残します。

## ゲートの記録（gate.json）

契約ごとの記録フォルダ `loop/legal/contracts/<契約 ID>/gate.json` に置きます。git には入れません。使う側のリポジトリの .gitignore に `loop/legal/contracts/` が要ります（無ければ道具が書く前に止まります）。相手のメールアドレスが入るので、プラグインの中にも git にも置きません。

```bash
T=<道具のフォルダの絶対パス>   # SKILL.md に出ているもの（Bash では ${CLAUDE_PLUGIN_ROOT} が置き換わらない）
C=loop/legal/contracts/<契約 ID>
# 入口で1回：相手の宛先と、届いたメールのスレッド・メッセージを登録する（返事が別スレッドで来たら足す）
python3 -I $T/gate.py watch $C --to <相手のアドレス> --thread <threadId> --message <messageId>
# 清書：検査に通ったら clean に記録する
python3 -I $T/make_clean.py $W/work --out $W/clean.docx --date <date> --record $C
# 下書きの確認：OK なら draft の「確認待ち」が消える
python3 -I $T/check_draft.py <get_draft の結果のファイル> --expect-attachments 0 --reply $W/reply.txt --record $C
# いまの記録を見る
python3 -I $T/gate.py status $C
```

## 利用側の設定の見本（二重の柵）

Hook に加えて、利用側のリポジトリの `.claude/settings.json` で、AI からのメールの送信そのものを禁じておくこともできます。設定ファイルは利用者が自分で書きます（プラグインは書きません）。`<Gmail のサーバー名>` は、`/mcp` などで見える Gmail コネクタの名前に置き換えます。

```json
{
  "permissions": {
    "deny": [
      "mcp__<Gmail のサーバー名>__send_message",
      "mcp__<Gmail のサーバー名>__reply",
      "mcp__<Gmail のサーバー名>__forward"
    ]
  }
}
```

- これを入れると、そのリポジトリでは、契約に関係の無いメールも AI からは送れなくなります。法務のデータだけを置くリポジトリなら、こちらも入れるのがおすすめです。
- LEGAL.md の書き換えは、外側のループで直すときに外す手間が要るので、設定ではなく Hook（ブランチ名で通す）に任せます。

## INCIDENT が起きたら（柵を1つ足す）

[specs/legal-001](../specs/legal-001-run-contract-loop.md) の「柵：INCIDENT → 柵を1つ足す」のとおり。新しい柵は、`scripts/tests/` に「作り話の契約で同じ失敗をわざと起こし、柵が止める」テストを足して、通ったら合格です。

## 試し方

```bash
python3 -I -m unittest discover -s "$T/tests"
```
