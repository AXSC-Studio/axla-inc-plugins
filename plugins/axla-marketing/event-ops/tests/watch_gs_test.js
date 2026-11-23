// spec 006：見張り（Apps Script）の判定部分の検証器。Node で、Gmail などを偽物に差し替えて動かす。
// 使い方：node watch_gs_test.js（失敗なら exit 1）
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const src = fs.readFileSync(path.join(__dirname, "..", "scripts", "apps-script", "watch_partner_mail.gs"), "utf8");

function sandbox({ inbound = [], sent = [], props = {}, fetchCode = 200 } = {}) {
  const store = Object.assign({}, props);
  const posts = [];
  const moved = [];
  const label = (name) => ({
    name,
    getThreads: () => (name.endsWith("/返信あり") ? inbound : []),
  });
  const ctx = {
    console: { log: () => {}, error: () => {} },
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => (k in store ? store[k] : null), setProperty: (k, v) => { store[k] = String(v); } }) },
    GmailApp: {
      getUserLabelByName: (n) => label(n),
      createLabel: (n) => label(n),
      search: (q) => sent,
    },
    UrlFetchApp: {
      fetch: (url, opts) => { posts.push(JSON.parse(opts.payload)); return { getResponseCode: () => fetchCode, getContentText: () => "ok" }; },
    },
    ScriptApp: { getProjectTriggers: () => [], newTrigger: () => ({ timeBased: () => ({ everyMinutes: () => ({ create: () => {} }) }) }) },
  };
  for (const t of inbound) {
    t.removeLabel = () => moved.push(["remove", t.getId()]);
    t.addLabel = () => moved.push(["add", t.getId()]);
  }
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  return { ctx, store, posts, moved };
}

const thread = (id, to = "venue@partner.example") => ({
  getId: () => id,
  getMessages: () => [{ getTo: () => to, getDate: () => new Date() }],
});
const BASE = { ROUTINE_URL: "https://example.invalid/fire", ROUTINE_TOKEN: "t", LABEL_PREFIX: "event-ops", PARTNER_DOMAINS: "partner.example,sponsor.example" };

// 1. 純粋な関数
{
  const { ctx } = sandbox();
  assert.strictEqual(ctx.domainOf("A <Venue@Partner.Example>"), "partner.example");
  assert.strictEqual(ctx.isPartnerRecipient("x@other.example, y@sponsor.example", ["partner.example", "sponsor.example"]), true);
  assert.strictEqual(ctx.isPartnerRecipient("x@other.example", ["partner.example"]), false);
  assert.deepStrictEqual(JSON.parse(ctx.buildPayload("reply", "T1")), { text: "event-ops kind=reply thread_id=T1" });
  assert.deepStrictEqual(ctx.trimDone(["a", "b", "c"], 2), ["b", "c"]);
}

// 2. 返事：ID だけ送り、ラベルを付け替える。同じ返事で2回起動しない
{
  const t = thread("T1");
  const s = sandbox({ inbound: [t], props: BASE });
  s.ctx.checkPartnerMail();
  assert.strictEqual(s.posts.length, 1);
  assert.ok(!JSON.stringify(s.posts[0]).includes("venue@"), "メールアドレスや本文を送らない");
  assert.deepStrictEqual(s.moved, [["remove", "T1"], ["add", "T1"]]);
  s.ctx.checkPartnerMail(); // ラベルが付け替わった前提でも、DONE_IDS で2回目は送らない
  assert.strictEqual(s.posts.length, 1);
}

// 3. 送信済み：相手のドメイン宛だけを拾う。ほかの宛先は拾わない
{
  const s = sandbox({ sent: [thread("S1", "venue@partner.example"), thread("S2", "friend@other.example")], props: BASE });
  s.ctx.checkPartnerMail();
  const kinds = s.posts.map((p) => p.text);
  assert.deepStrictEqual(kinds, ["event-ops kind=sent thread_id=S1"]);
}

// 4. 送れなかったら、ラベルも処理済みも残さない（次の1分でもう一度）
{
  const t = thread("T9");
  const s = sandbox({ inbound: [t], props: BASE, fetchCode: 500 });
  s.ctx.checkPartnerMail();
  assert.deepStrictEqual(s.moved, []);
  assert.ok(!(s.store.DONE_IDS || "").includes("T9"));
}

// 5. 設定が無ければ止まる（合鍵はコードに書かない）
{
  const s = sandbox({ props: {} });
  assert.throws(() => s.ctx.checkPartnerMail(), /ROUTINE_URL/);
}

console.log("watch_partner_mail.gs: all passed");
