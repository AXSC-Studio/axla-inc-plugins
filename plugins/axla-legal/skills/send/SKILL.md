---
name: send
description: Part of Axla Legal, normally called from /axla-legal:loop. After the CEO's final OK, builds the clean copy and reply text with tools, creates the reply draft, and runs the pre-send check; it cannot move on until the check passes. Sending stays with a person. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。代表の最終 OK のあと、清書と返信文を道具で作り、返信の下書きを作り、送る前の検査を通す。検査に通らないと先へ進めない。送信は人が押す。
---

# send（送る準備）

道具：`${CLAUDE_PLUGIN_ROOT}/scripts`。決まりは spec の「送る前のゲート」。柵（Hook）が飛ばしを止める。

1. 清書：`make_clean.py <work> --out <W>/clean.docx --date <date> --record <記録フォルダ>`。PDF に書き出して1回だけ目で確かめ、Drive の契約フォルダに `…_vX.Y.Z_Axla Comments.docx` で置く。
2. 返信文：`make_reply.py "<記録フォルダ>/Redline Data.json" --out-text <W>/reply.txt --out-html <W>/reply.html --record <記録フォルダ>`。手で書かない。
3. 下書き：Gmail のつながりの `create_draft`（相手のメールのスレッドへの返信。添付なし・画像なし）。
4. 検査：`get_draft` を `messageFormat=RAW` で読む。Hook がその場で検査して記録する。NG なら直す（引用の画像は、代表に Gmail の画面で消してもらう）。
5. 代表に「下書きができた。清書を添付して送ってほしい」と知らせて止まる（人間ゲート「送信」）。
6. 代表が送ったと言ったら、送信済みのメールを `get_message`（RAW）で読む。Hook が送った後の検査をする。台帳を「相手の返事待ち」にする。
7. 作業フォルダ（展開した本文・清書・返信文）を消す（`rm -rf <W>`）。本文を手元に残さない。記録フォルダは消さない。
