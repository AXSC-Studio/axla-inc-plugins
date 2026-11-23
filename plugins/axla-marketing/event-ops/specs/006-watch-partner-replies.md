# 006 · watch partner replies（返事と送信済みの見張り）

> 相手の返事と、人が送ったことを、人が気づく前に拾って記録し、知らせる。見張りは読むだけ

**実装**: `scripts/apps-script/watch_partner_mail.gs`・`prompts/routine-triage.md`・`prompts/routine-morning.md`・`adapters/email/{manual,gmail}.md`
**起源**: 001 の中間の起動役。先行プラグインの返事の見張り（ラベル → Apps Script → ルーティン、ID だけ送る）の試運転の学び
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

---

## 1. Specify
- gmail：フィルタで相手のメールにラベルを付ける → Apps Script（1分ごと）がラベルのスレッドと、承認 ID ラベルの付いた送信済みを見つける → ルーティンの /fire にスレッド ID だけ POST → 成功したらラベルを付け替える。
- ルーティンが使える道具は、メールの読む道具だけ（書き込みは `disallowed_tools` で禁止）。返すのは「どのイベント・どの相手・答える点・計画に効くか」の要約だけ。
- 朝の予備起動で、返事待ちが `reply_wait_days`（初期値 3）を超えた件数と、送信済みの件数を知らせる。記録をどこかへ push しない。
- manual：人が「送った」「返事が来た」を入れる。
- 合鍵は Apps Script のスクリプトのプロパティに人が貼る。コードにも git にも書かない。

受け入れ条件
- [ ] 同じ返事で2回起動しない
- [ ] ルーティンの設定に書き込みの道具が無い
- [ ] 送信済みを拾ったとき、partners.csv の状態が「送った」になる

## 2〜3. Plan
- 返事が別スレッドで来ることがある。スレッド ID だけでなく、相手のドメインと日時でも探す。

## 4. Tasks
- watch_partner_mail.gs → routine-triage.md → routine-morning.md
