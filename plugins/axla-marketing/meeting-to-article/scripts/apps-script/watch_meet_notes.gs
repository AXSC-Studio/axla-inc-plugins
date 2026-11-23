/**
 * Meeting to Article（marketing）: 一人の Meet の Gemini メモができたら、クラウドのルーティンを起こす。
 *
 * しくみ
 *   このスクリプト（1分ごと）が、Drive で題が MEETING_TITLE で始まり「Gemini によるメモ」を含む
 *   Google ドキュメントを、最後に見た時刻より新しいものだけ探す
 *   → まだ処理していないドキュメント ID なら、ルーティンの /fire に POST（本文は ID だけ。メモの中身は送らない）
 *   → 成功したら ID を処理済みに入れる（同じメモで何度も起こさない。失敗したら次の1分でもう一度）
 *   ファイルの名前は変えない・動かさない（ほかの定期タスクが名前を付け替えても、ID は変わらない）
 *
 * 設定（スクリプトのプロパティ。コードには書かない）
 *   ROUTINE_URL   … ルーティンの /fire の URL（人が貼る）
 *   ROUTINE_TOKEN … ルーティンの API の合鍵（人が貼る）
 *   MEETING_TITLE … 収録に使う Meet の題（例：コラム）
 */
const NOTES_MARK = 'Gemini によるメモ';
const LOOKBACK_MS = 2 * 24 * 60 * 60 * 1000; // 初回に見る範囲
const KEEP_IDS = 200;

function checkNotes() {
  const props = PropertiesService.getScriptProperties();
  const url = props.getProperty('ROUTINE_URL');
  const token = props.getProperty('ROUTINE_TOKEN');
  const title = props.getProperty('MEETING_TITLE');
  if (!url || !token || !title) throw new Error('ROUTINE_URL・ROUTINE_TOKEN・MEETING_TITLE をスクリプトのプロパティに入れてください');

  const since = new Date(Number(props.getProperty('LAST_SCAN') || Date.now() - LOOKBACK_MS));
  const startedAt = Date.now();
  const done = JSON.parse(props.getProperty('DONE_IDS') || '[]');

  const q = "mimeType = 'application/vnd.google-apps.document'" +
    " and title contains '" + esc(title) + "'" +
    " and title contains '" + esc(NOTES_MARK) + "'" +
    " and createdDate > '" + since.toISOString() + "'" +
    ' and trashed = false';
  const it = DriveApp.searchFiles(q);
  let ok = true;
  while (it.hasNext()) {
    const f = it.next();
    const id = f.getId();
    // 題が MEETING_TITLE で始まるもの、または yyyymmdd_ を付けられたあとのものだけ
    if (!new RegExp('^(\\d{8}_)?' + reEsc(title)).test(f.getName())) continue;
    if (done.indexOf(id) >= 0) continue;
    const res = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        Authorization: 'Bearer ' + token,
        'anthropic-beta': 'experimental-cc-routine-2026-04-01',
        'anthropic-version': '2023-06-01',
      },
      payload: JSON.stringify({ text: 'meeting-to-article doc_id=' + id }),
      muteHttpExceptions: true,
    });
    const code = res.getResponseCode();
    if (code >= 200 && code < 300) {
      done.push(id);
      console.log('fired: ' + id);
    } else {
      ok = false; // LAST_SCAN を進めず、次の1分でもう一度
      console.error('fire failed ' + code + ': ' + res.getContentText());
    }
  }
  props.setProperty('DONE_IDS', JSON.stringify(done.slice(-KEEP_IDS)));
  if (ok) props.setProperty('LAST_SCAN', String(startedAt - 60 * 1000)); // 1分重ねて取りこぼしを防ぐ
}

function esc(s) { return s.replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }
function reEsc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

/** 最初に1回だけ手で実行：1分ごとのトリガーを作る */
function install() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'checkNotes') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('checkNotes').timeBased().everyMinutes(1).create();
}
