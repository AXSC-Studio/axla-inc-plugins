/**
 * event-ops（axla-marketing）：相手の返事と、人が送ったことを拾って、クラウドの見張りのルーティンを起こす。spec 006。
 *
 * しくみ（1分ごと）
 *   返事：Gmail のフィルタが、相手のドメインからのメールに「<LABEL_PREFIX>/返信あり」を付ける
 *         → このスクリプトがそのスレッドを見つけ、ルーティンの /fire に「kind=reply thread_id=…」だけ POST
 *         → 成功したら「<LABEL_PREFIX>/通知済み」に付け替える
 *   送信：人が送った送信済みのうち、宛先が PARTNER_DOMAINS のドメインのものを拾い「kind=sent thread_id=…」を POST
 *   同じ通知を2回送らない：「スレッド ID ＋そのスレッドの通数」を処理済みに覚える（同じスレッドの2通目の返事は知らせる）
 *   送れなかったら、ラベルも処理済みも残さない（次の1分でもう一度）
 *   メールの中身・アドレス・名前は送らない。相手の番号への対応付けは、手元の match_partner.py が names.local で行う
 *
 * 設定（スクリプトのプロパティ。コードにも git にも書かない。人が貼る）
 *   ROUTINE_URL     … ルーティンの /fire の URL
 *   ROUTINE_TOKEN   … ルーティンの API の合鍵
 *   LABEL_PREFIX    … ラベルの頭（初期値 event-ops）
 *   PARTNER_DOMAINS … 相手のドメインをカンマ区切りで（例 partner.example,sponsor.example）。空なら送信済みは見ない
 */
var KEEP_DONE = 300;

function domainOf(addr) {
  var m = String(addr || "").match(/@([A-Za-z0-9.-]+\.[A-Za-z]{2,})/);
  return m ? m[1].toLowerCase() : "";
}

function isPartnerRecipient(to, domains) {
  var parts = String(to || "").split(",");
  for (var i = 0; i < parts.length; i++) {
    if (domains.indexOf(domainOf(parts[i])) >= 0) return true;
  }
  return false;
}

function buildPayload(kind, threadId) {
  return JSON.stringify({ text: "event-ops kind=" + kind + " thread_id=" + threadId });
}

function trimDone(list, keep) {
  return list.length > keep ? list.slice(list.length - keep) : list;
}

function fire_(url, token, payload) {
  var res = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + token,
      "anthropic-beta": "experimental-cc-routine-2026-04-01",
      "anthropic-version": "2023-06-01",
    },
    payload: payload,
    muteHttpExceptions: true,
  });
  var code = res.getResponseCode();
  if (code >= 200 && code < 300) return true;
  console.error("fire failed " + code + ": " + res.getContentText());
  return false;
}

function checkPartnerMail() {
  var props = PropertiesService.getScriptProperties();
  var url = props.getProperty("ROUTINE_URL");
  var token = props.getProperty("ROUTINE_TOKEN");
  if (!url || !token) throw new Error("ROUTINE_URL・ROUTINE_TOKEN をスクリプトのプロパティに入れてください");
  var prefix = props.getProperty("LABEL_PREFIX") || "event-ops";
  var domains = String(props.getProperty("PARTNER_DOMAINS") || "")
    .split(",").map(function (d) { return d.trim().toLowerCase(); }).filter(function (d) { return d; });
  var done = JSON.parse(props.getProperty("DONE_IDS") || "[]");

  var labelNew = GmailApp.getUserLabelByName(prefix + "/返信あり") || GmailApp.createLabel(prefix + "/返信あり");
  var labelDone = GmailApp.getUserLabelByName(prefix + "/通知済み") || GmailApp.createLabel(prefix + "/通知済み");

  var threads = labelNew.getThreads(0, 20);
  for (var i = 0; i < threads.length; i++) {
    var t = threads[i];
    var key = "reply:" + t.getId() + ":" + t.getMessages().length;
    if (done.indexOf(key) >= 0 || fire_(url, token, buildPayload("reply", t.getId()))) {
      t.removeLabel(labelNew);
      t.addLabel(labelDone);
      if (done.indexOf(key) < 0) done.push(key);
    }
  }

  if (domains.length) {
    var sent = GmailApp.search("in:sent newer_than:2d", 0, 30);
    for (var j = 0; j < sent.length; j++) {
      var s = sent[j];
      var msgs = s.getMessages();
      var last = msgs[msgs.length - 1];
      if (!isPartnerRecipient(last.getTo(), domains)) continue;
      var skey = "sent:" + s.getId() + ":" + msgs.length;
      if (done.indexOf(skey) >= 0) continue;
      if (fire_(url, token, buildPayload("sent", s.getId()))) done.push(skey);
    }
  }
  props.setProperty("DONE_IDS", JSON.stringify(trimDone(done, KEEP_DONE)));
}

/** 最初に1回だけ手で実行：1分ごとのトリガーを作る */
function install() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === "checkPartnerMail") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("checkPartnerMail").timeBased().everyMinutes(1).create();
}
