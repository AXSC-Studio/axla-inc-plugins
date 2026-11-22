# marketing-001 · turn meeting into article
> 一人の Google Meet でしゃべった Gemini メモを、熱が冷める前にサイトの記事の下書きとアイキャッチにする決まり。道具はこのプラグイン、利用側のデータ（設定・用語集・トーンの見本）は利用側の `loop/meet-to-article/` に分ける

**実装対象**: scripts/（道具）・prompts/（指示文）・利用側の loop/meet-to-article/（config.json・glossary.md・tone/）
**起源**: 2026-11-20 の初収録（ループエンジニアリング論、5分15秒）と、2026-11-21 の設計ディベート（4案＋反論2人、代表承認）
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

---

## Requirements

- The system shall 新しい Gemini メモを、Drive のドキュメント ID で見つけること。ファイル名やフォルダの場所を目印にしないこと
- The system shall 処理済みのドキュメント ID を台帳に残し、同じメモで二度動かないこと
- The system shall 記事を「しゃべりの編集」として書くこと。本人が言っていない主張・数字・体験を足さないこと
- The system shall 利用側の tone/ の「声」（一人称・文体・入り方・太字の決め台詞）をまね、「形」（字数・グラフ・写真の数）はまねないこと。字数は config の範囲（初期値 1500〜2500字）に収めること
- The system shall 太字の決め台詞を、本人が実際に言った言葉から選ぶこと
- The system shall 誤変換を glossary.md で直し、直しきれないものを「要確認」に挙げること
- The system shall 荒い言葉を穏やかに言い換え、取引先・個人の名前を伏せ、言い換えた所と伏せた所を「要確認」に並べること
- The system shall 記事の URL（slug）だけを英語にすること（`yyyy-mm-dd-english-words`、すべて小文字）
- The system shall 記事を status: draft で作り、同じ slug の記事が既にあれば止めること（上書きしない）
- The system shall 通知のいちばん上に「要確認」を置き、その下に題・リード・下書きの場所を書くこと
- The system shall NOT 記事を公開すること。公開は人が押す
- The system shall NOT config で許されていない有料の API を呼ぶこと（初期値は無料の文字だけのアイキャッチ）
- The system shall NOT Drive のメモの名前を変えたり、動かしたり、消したりすること

## Non-goals

- 本番の CMS への書き込みの仕組み（利用側のリポジトリの決まりと CI で行う。道具は下書きのファイルを作るところまで）
- 英語版・音声（公開したあとに利用側の別の仕組みで付ける）
- 複数人の会議の議事録（このプラグインは一人の収録だけを扱う）

## Acceptance Criteria

- [ ] 同じドキュメント ID を2回渡しても、2本目の下書きができない
- [ ] 下書きの JSON の status が draft で、既にある slug では `make_post.py` が止まる
- [ ] 本文の字数が config の範囲に入っている
- [ ] 太字の決め台詞が、文字起こしの中に（誤変換を直した形で）ある
- [ ] 通知のいちばん上に「要確認」があり、言い換え・伏せ字・直しきれない誤変換が 0件なら「なし」と書いてある
- [ ] アイキャッチが config の大きさで、題と日付が読める
- [ ] Drive のメモの名前と場所が、処理の前と後で同じ

---

## 流れ

```
人：一人の Meet「<config.meeting_title>」に入り、Gemini メモをオンにしてしゃべり、退出する
  → 見張り（scripts/apps-script/watch_meet_notes.gs、1分ごと）が新しいメモをドキュメント ID で見つける
  → クラウドのルーティンの /fire に POST する。本文はドキュメント ID だけ（メモの中身は送らない）
  → ルーティンがこのスキルで：メモを読む → 誤変換を直す → 編集して記事にする → 検証役が見る → 直す
  → scripts/make_eyecatch.py でアイキャッチ、scripts/make_post.py で下書きの JSON を作る
  → 利用側の決まり（Axla は CI）で、本番の CMS に下書きとして入る
  → 通知（Slack の DM など）を1通送る
人：管理画面で読んで、公開を押す
```

## 内側のループ（編集 → 検証）

| 役 | 見るもの | 止める条件 |
|---|---|---|
| 編集役 | 文字起こし・glossary.md・tone/ | — |
| 検証役（並列） | 脚色（言っていないことを足していないか）・トーン・伏せ字と言い換え・字数 | 致命的 0件。3周しても 0件にならなければ、下書きは作り、通知の「要確認」に残りを書く |

指示文は prompts/editor-prompts.md。

## 決めていないこと（宿題）

- Gemini メモができるまでの時間（収録の退出から何分か）
- アイキャッチを本番に出す置き場（デプロイ待ちをなくしたい。Axla は Firebase Storage を検討中）
- スマホから管理画面で公開を押せるか
