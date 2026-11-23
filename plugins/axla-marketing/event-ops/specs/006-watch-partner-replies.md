# 006 · watch partner replies（返事と送信済みの見張り）

> 相手の返事と、人が送ったことを、人が気づく前に拾って記録し、知らせる。見張りは読むだけ

**実装**: `event-ops/scripts/apps-script/watch_partner_mail.gs`・`scripts/match_partner.py`・`prompts/routine-triage.md`・`prompts/routine-morning.md`・`adapters/email/`（manual・gmail・routine.example.json）・`tests/test_watch.py`・`tests/watch_gs_test.js`
**起源**: 001 の中間の起動役。先行プラグインの返事の見張り（ラベル → Apps Script → ルーティン、ID だけ送る）の試運転の学び
**ステータス**: L2（実装・テスト済み。Gmail とルーティンの設定は人間ゲート）

---

## 1. Specify
- gmail：フィルタで相手のメールにラベルを付ける → Apps Script（1分ごと）がラベルのスレッドと、相手のドメイン宛の送信済み（`PARTNER_DOMAINS`）を見つける → ルーティンの /fire に種類とスレッド ID だけ POST → 成功したらラベルを付け替える。処理済みは「スレッド ID ＋通数」で覚える（同じスレッドの2通目の返事は知らせる）。
- ルーティンは名前の表（names.local）を持たない。相手の番号への対応付けは、手元の `match_partner.py` が行う。
- ルーティンが使える道具は、メールの読む道具だけ（書き込みは `disallowed_tools` で禁止）。返すのは「どのイベント・どの相手・答える点・計画に効くか」の要約だけ。
- 朝の予備起動で、返事待ちが `reply_wait_days`（初期値 3）を超えた件数と、送信済みの件数を知らせる。記録をどこかへ push しない。
- manual：人が「送った」「返事が来た」を入れる。
- 合鍵は Apps Script のスクリプトのプロパティに人が貼る。コードにも git にも書かない。

受け入れ条件
- [x] 同じ返事で2回起動しない。同じスレッドの2通目の返事は知らせる。送れなかったら処理済みにしない（`watch_gs_test.js`）
- [x] ルーティンの設定の見本に書き込みの道具が無い（`test_routine_example_disallows_write_tools`）
- [x] 送信済みは相手のドメイン宛だけを拾い、ID だけ送る（`watch_gs_test.js`）。手元で `match_partner.py` が番号に直し、`update_partners.py sent` で台帳が「送った」になる（005 のテスト）
- [ ] 人間ゲート：Gmail のフィルタ・Apps Script・ルーティンを実際につないで、返事1通で知らせが来るかの試運転

## 2〜3. Plan
- 返事が別スレッドで来ることがある。スレッド ID だけでなく、相手のドメインと日時でも探す。

## 4. Tasks
- [x] watch_partner_mail.gs（判定部分は Node でテスト）
- [x] match_partner.py
- [x] routine-triage.md・routine-morning.md・routine.example.json
- [ ] 人間ゲート：つなぐ試運転（合鍵を貼るのは人）
