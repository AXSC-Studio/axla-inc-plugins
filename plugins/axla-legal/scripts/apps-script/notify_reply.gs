/**
 * Axla Legal（redline-contract）: 相手の返事を見つけたら、クラウドの見張りタスクを起こす。
 *
 * しくみ
 *   Gmail のフィルタが、相手からのメールに「Legal/返信あり」のラベルを付ける
 *   → このスクリプト（1分ごと）がそのラベルのスレッドを見つける
 *   → 見張りタスクの /fire に POST（本文はスレッド ID だけ。メールの中身は送らない）
 *   → ラベルを「Legal/通知済み」に付け替える（同じ返事で何度も起こさない）
 *
 * 設定（スクリプトのプロパティ。コードには書かない）
 *   ROUTINE_URL   … 見張りタスクの /fire の URL（タスク画面の API の欄に出る。代表が貼る）
 *   ROUTINE_TOKEN … claude.ai のタスク画面で発行した API の合鍵（代表が貼る）
 */
const LABEL_NEW = 'Legal/返信あり';
const LABEL_DONE = 'Legal/通知済み';

function checkReplies() {
  const props = PropertiesService.getScriptProperties();
  const ROUTINE_URL = props.getProperty('ROUTINE_URL');
  const token = props.getProperty('ROUTINE_TOKEN');
  if (!ROUTINE_URL) throw new Error('ROUTINE_URL がスクリプトのプロパティにありません');
  if (!token) throw new Error('ROUTINE_TOKEN がスクリプトのプロパティにありません');

  const labelNew = GmailApp.getUserLabelByName(LABEL_NEW) || GmailApp.createLabel(LABEL_NEW);
  const labelDone = GmailApp.getUserLabelByName(LABEL_DONE) || GmailApp.createLabel(LABEL_DONE);

  const threads = labelNew.getThreads(0, 20);
  threads.forEach(function (thread) {
    const res = UrlFetchApp.fetch(ROUTINE_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        Authorization: 'Bearer ' + token,
        'anthropic-beta': 'experimental-cc-routine-2026-04-01',
        'anthropic-version': '2023-06-01',
      },
      payload: JSON.stringify({ text: 'Gmail thread_id=' + thread.getId() }),
      muteHttpExceptions: true,
    });
    const code = res.getResponseCode();
    if (code >= 200 && code < 300) {
      thread.removeLabel(labelNew);
      thread.addLabel(labelDone);
      console.log('fired: ' + thread.getId() + ' ' + res.getContentText());
    } else {
      // 失敗したらラベルを残し、次の1分でもう一度試す
      console.error('fire failed ' + code + ': ' + res.getContentText());
    }
  });
}

/** 最初に1回だけ手で実行：1分ごとのトリガーを作る */
function install() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'checkReplies') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('checkReplies').timeBased().everyMinutes(1).create();
}
