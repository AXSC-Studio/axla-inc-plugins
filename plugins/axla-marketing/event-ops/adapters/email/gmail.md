# ~~email = gmail（返事と送信済みの見張り）

## つなぐ（人間ゲート・1回だけ）
1. Gmail のフィルタ：相手のドメインからのメールに、ラベル `event-ops/返信あり` を付ける
2. claude.ai のクラウドのルーティンを作る。設定は [routine.example.json](routine.example.json)（道具は読むだけ。書き込みは disallowed_tools で止める）。指示文は `prompts/routine-triage.md`、毎朝の予備の起動は `prompts/routine-morning.md`
3. Apps Script（`scripts/apps-script/watch_partner_mail.gs`）を作り、スクリプトのプロパティに `ROUTINE_URL`・`ROUTINE_TOKEN`・`PARTNER_DOMAINS` を人が貼る。`install()` を1回実行して、1分ごとのトリガーを作る

## 流れ
- 返事：ラベル → Apps Script が `kind=reply thread_id=…` だけをルーティンへ → ルーティンが読んで要約を知らせる
- 送信済み：相手のドメイン宛の送信済みを Apps Script が拾い、`kind=sent thread_id=…` をルーティンへ
- 手元：知らせを受けたら、coordinate-partners が `match_partner.py` でアドレスを相手の番号に直し、`update_partners.py replied|sent` で台帳を進める（名前の表は手元にだけある）

## 決めごと
- 送るのは ID だけ。メールの中身・アドレス・名前はクラウドへ送らない
- 合鍵はスクリプトのプロパティに人が貼る。コードにも git にも書かない
- 返事が別のスレッドで来ることがある。スレッド ID だけでなく、相手のドメインと日時でも探す
