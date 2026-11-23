# ~~docs = artifact（claude.ai の Artifact）

1. 資料ごとに Artifact を作る。名前は `yyyymmdd_english-name_v1.0`（例：`20261211_sponsor-deck_v1.0`）
2. 中身の数は plan.md・budget.md から取る。社内の目的・目標の線は入れない
3. 作った URL を `kit/<資料>.url` に1行で書き、`checklist.py mark --item <資料> --evidence kit/<資料>.url`
4. 相手に送るときは、その版を**凍結**する（spec 005 の freeze_kit.py：版ごとに別の URL、送ったあとは上書きしない。上書きの公開は spec 002 の hook が止める）
5. 直すときは版を上げて新しい URL で作る（`_v1.1`）
