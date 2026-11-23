# Changelog (Axla Legal)

**English** | [日本語](#日本語)

Versions follow [Semantic Versioning](https://semver.org/). Every version bump adds an entry here (CI checks it). Release tags are `axla-legal--vX.Y.Z`, made with `claude plugin tag`; pushing a tag is a human gate.

## Road to 1.0.0
1.0.0 means "we will not break outside users without notice". It is released when all of these hold:
- Every axla-legal issue from #5 to #37 is closed, or has a written reason for not doing it.
- CI is green on `main` (tests, `claude plugin validate --strict`, repository checks).
- One real contract has gone through the whole loop to Signed and the outer loop (tracking issue #31, step 6).
- The listing information, privacy policy and icon are in place (#18, #23, #24).

## 0.17.0
- Reply watcher: versioned routine settings (blocked tools, prompt that treats mail as data, spoofing rule, test with an instruction-laden dummy mail); Apps Script scopes, lock, minimal logs, beta header as a property (#28).

## 0.16.1
- Added this changelog and the 1.0.0 conditions; CI now checks that a version bump has a changelog entry (#29).

## 0.16.0
- Comments and the format check are written in the plugin itself (`add_comments.py`, `validate_docx.py`); no outside skill or virtual environment (#8, #9).

## 0.15.0
- No hard-coded company: author name and company name come from the user's `loop/legal/config.json`; reviewer prompts use placeholders (#5, #6, #7, #25).

## 0.14.0
- Directory listing preparation: README requirements, data and network, data handling, troubleshooting; plugin.json listing fields; `PRIVACY.md`; `LICENSE` in the plugin folder (#23, #24).

## 0.13.0
- Starter kit: fictional NDA, sample redline and review, templates, "try it in 5 minutes", example prompts (#17).

## 0.12.0
- One entry `/axla-legal:loop` and parts `intake`, `redline-contract`, `review`, `gdoc`, `send`, `learn`; `loop.py` decides the next step; the internal Google Doc is created once with the Drive connector (#13, #26, #33, #36).

## 0.11.0
- Reference errors are found by `check_refs.py` and always counted as critical (#35).

## 0.10.0
- Contract files are kept out of the user's git: records refuse to be written unless ignored; hooks block adding or committing contract files (#22).

## 0.9.0
- The clean-copy check covers headers, footers, footnotes, moves, format changes and side information; small tools no longer stop half-way (#21, #27).

## 0.8.0
- The pre-send check runs on every draft read as RAW, and fails with zero correction lines (#20, #34).

## 0.7.0
- Templates exported from Google Docs can be redlined (#32).

## 0.6.0
- Outer loop procedure, `outer_loop.py`, `count_findings.py`, reviewer prompts 2.0.0 (#16).

## 0.5.0
- Budget limits and the out-of-budget exit; `budget.py` (#15).

## 0.4.0
- Hooks enforce the pre-send gate and the closed world; `gate.py` (#10, #14).

## 0.3.0
- The clean-copy tool leaves no file when a check fails (#11).

## 0.2.x
- Renamed from `legal-loop` to `axla-legal`; English metadata and bilingual READMEs.

---

## 日本語

# 変更履歴（Axla Legal）

版は [Semantic Versioning](https://semver.org/lang/ja/) で付けます。版を上げるたびに、ここに1つ足します（CI が確かめます）。リリースのタグは `axla-legal--vX.Y.Z` で、`claude plugin tag` で作ります。タグの push は人間ゲートです。

## 1.0.0 への道
1.0.0 は「外の利用者を、予告なしに壊さない」と約束する版です。次をすべて満たしたら出します。
- axla-legal の Issue #5〜#37 が、すべて閉じているか、やらない理由が書いてある。
- `main` で CI が緑（テスト・`claude plugin validate --strict`・リポジトリの検査）。
- 本物の契約1件が、署名（Signed）と外側のループまで、ループを1周した（まとめの #31 の6番目）。
- 掲載の情報・プライバシーポリシー・アイコンがそろっている（#18・#23・#24）。

## 0.17.0
- 返事の見張り：止める道具・メールの本文をデータとして扱うプロンプト・なりすましの扱い・指示入りのダミーのメールでの試し方を、版付きで置いた。Apps Script は権限を絞り、二重起動を止め、ログを最小にし、beta の値をプロパティに出した（#28）。

## 0.16.1
- この変更履歴と 1.0.0 の条件を足した。版を上げたら変更履歴に書いてあるかを、CI が確かめる（#29）。

## 0.16.0
- コメントの書き込みと形式の検査を、プラグインの中で行う（`add_comments.py`・`validate_docx.py`）。外のスキルも venv も要らない（#8・#9）。

## 0.15.0
- 会社名の決め打ちをなくした。作成者名と自社名は、利用側の `loop/legal/config.json` から読む。指示文は差し込みにした（#5・#6・#7・#25）。

## 0.14.0
- 掲載の準備：README の前提・通信先・データの扱い・困ったとき、plugin.json の掲載用の項目、`PRIVACY.md`、プラグインのフォルダの `LICENSE`（#23・#24）。

## 0.13.0
- お試しセット：作り話の NDA、直しと検証の見本、ひな形、5分で試す、例のプロンプト（#17）。

## 0.12.0
- 入口 `/axla-legal:loop` と、部品 `intake`・`redline-contract`・`review`・`gdoc`・`send`・`learn`。`loop.py` が次の1歩を決める。社内用の Google ドキュメントは、ドライブのつながりで1回だけ作る（#13・#26・#33・#36）。

## 0.11.0
- 参照の誤りを `check_refs.py` で見つけ、必ず致命的として数える（#35）。

## 0.10.0
- 契約ファイルを利用側の git に入れない：除外に入っていなければ記録を書かない。Hook が契約ファイルの add・commit を止める（#22）。

## 0.9.0
- 清書の検査を、ヘッダー・フッター・脚注・移動・書式の変更・付随の情報まで広げた。小さな道具が途中で半端に終わらない（#21・#27）。

## 0.8.0
- 送る前の検査は、RAW で読んだ下書きのたびに走り、修正点0行で止まる（#20・#34）。

## 0.7.0
- Google ドキュメントから書き出した雛形でも、直しを入れられる（#32）。

## 0.6.0
- 外側のループの手順、`outer_loop.py`、`count_findings.py`、指示文 2.0.0（#16）。

## 0.5.0
- 予算の上限と「予算切れ」の出口、`budget.py`（#15）。

## 0.4.0
- Hook が、送る前のゲートと閉じた世界を止める。`gate.py`（#10・#14）。

## 0.3.0
- 清書の道具は、検査に通らなければファイルを残さない（#11）。

## 0.2.x
- `legal-loop` から `axla-legal` に改名。英語のメタデータと、英日の README。
