---
name: gdoc
description: Part of Axla Legal, normally called from /axla-legal:loop. After the inner loop passes, creates the internal Google Doc (suggestions and comments) once for the CEO to review. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。内側のループが通ったあとに1回だけ、代表が見る社内用の Google ドキュメント（提案とコメント入り）を作る。
---

# gdoc（社内用の gdoc を作る）

内側のループの周回は手元の .docx で回し、gdoc は**最後に1回だけ**作る（Issue #33。gcloud は使わない）。

1. 変更履歴とコメントの入った .docx（redline.docx）を、Google ドライブのつながりの `create_file` で、Drive の契約フォルダに Google ドキュメントとして作る。名前は `<契約フォルダ名>_vX.Y.Z_<自社名> Comments`。
2. 前に作った同じ版の gdoc があれば、ゴミ箱に移す（中身は新しい gdoc にある。リンクは変わる）。
3. 記録する：`python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/gate.py mark <記録フォルダ> gdoc --id <作った gdoc の ID>`。
4. 代表に、gdoc のリンクと「何を変えたか」を3行で知らせて止まる（人間ゲート「最終 OK」）。
5. 代表が「最終 OK」と言ったら `gate.py mark <記録フォルダ> approval`。直しを頼まれたら redline-contract に戻る（gdoc はまた最後に作り直す）。
