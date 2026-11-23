/**
 * Axla Legal: 相手の返事を見つけたら、クラウドの見張りタスクを起こす。
 *
 * 試験中：claude.ai のタスクの API（beta）を使う。予告なく動かなくなることがある。
 * 権限は appsscript.json で絞る（Gmail のラベル・外への通信・トリガー・自分あてのメール・自分のアドレス）。
 * 見張りタスクの設定（止める道具・プロンプト）は routines/reply-watcher.md。
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
 *   MAX_RETRIES   … 起こすのに失敗してよい回数（予算。loop/legal/budget.json の notify_retries と同じ値）。
 *                   貼らなければ「上限なし」（失敗したら次の1分でまた試す）。上限に来たら、そのスレッドは
 *                   ラベル「Legal/通知失敗」に移して試すのをやめ、自分あてにメールで知らせる
 *   ROUTINE_BETA  … beta のヘッダーの値（省くと下の既定値）。beta が変わったら、コードではなくここを直す
 *
 * ログには、スレッド ID と HTTP のステータスだけを残す（応答の本文やメールの中身は残さない）。
 */
const DEFAULT_BETA = 'experimental-cc-routine-2026-04-01';
const LABEL_NEW = 'Legal/返信あり';
const LABEL_DONE = 'Legal/通知済み';
const LABEL_FAILED = 'Legal/通知失敗';

function checkReplies() {
  // 1分ごとのトリガーが重なっても、二重に起こさない
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) {
    console.log('skip: 前の実行がまだ動いている');
    return;
  }
  try {
    run_();
  } finally {
    lock.releaseLock();
  }
}

function run_() {
  const props = PropertiesService.getScriptProperties();
  const ROUTINE_URL = props.getProperty('ROUTINE_URL');
  const token = props.getProperty('ROUTINE_TOKEN');
  if (!ROUTINE_URL) throw new Error('ROUTINE_URL がスクリプトのプロパティにありません');
  if (!token) throw new Error('ROUTINE_TOKEN がスクリプトのプロパティにありません');
  const maxRaw = props.getProperty('MAX_RETRIES');
  const maxRetries = maxRaw ? parseInt(maxRaw, 10) : null; // null＝上限なし

  const labelNew = GmailApp.getUserLabelByName(LABEL_NEW) || GmailApp.createLabel(LABEL_NEW);
  const labelDone = GmailApp.getUserLabelByName(LABEL_DONE) || GmailApp.createLabel(LABEL_DONE);

  const threads = labelNew.getThreads(0, 20);
  threads.forEach(function (thread) {
    const res = UrlFetchApp.fetch(ROUTINE_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        Authorization: 'Bearer ' + token,
        'anthropic-beta': props.getProperty('ROUTINE_BETA') || DEFAULT_BETA,
        'anthropic-version': '2023-06-01',
      },
      payload: JSON.stringify({ text: 'Gmail thread_id=' + thread.getId() }),
      muteHttpExceptions: true,
    });
    const code = res.getResponseCode();
    if (code >= 200 && code < 300) {
      thread.removeLabel(labelNew);
      thread.addLabel(labelDone);
      props.deleteProperty('fail_' + thread.getId());
      console.log('fired: ' + thread.getId() + ' ' + code);
    } else {
      // 失敗したらラベルを残し、次の1分でもう一度試す。上限（MAX_RETRIES）に来たら止めて知らせる
      const key = 'fail_' + thread.getId();
      const fails = parseInt(props.getProperty(key) || '0', 10) + 1;
      props.setProperty(key, String(fails));
      console.error('fire failed: ' + thread.getId() + ' ' + code + ' (' + fails + '/' + (maxRetries === null ? '上限なし' : maxRetries) + ')');
      if (maxRetries !== null && fails >= maxRetries) {
        const labelFailed = GmailApp.getUserLabelByName(LABEL_FAILED) || GmailApp.createLabel(LABEL_FAILED);
        thread.removeLabel(labelNew);
        thread.addLabel(labelFailed);
        props.deleteProperty(key);
        // 本文はスレッド ID と回数だけ（メールの中身は書かない）
        MailApp.sendEmail(Session.getEffectiveUser().getEmail(), 'Legal：予算切れ（自動検知の再試行）',
          '見張りタスクを ' + fails + ' 回起こせなかったので、試すのをやめた。\nthread_id=' + thread.getId() +
          '\nラベル「' + LABEL_FAILED + '」のスレッドを人が見て、見張りタスクを手で起こす。');
      }
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
