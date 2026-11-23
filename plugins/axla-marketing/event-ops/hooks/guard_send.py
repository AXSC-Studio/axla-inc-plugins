#!/usr/bin/env python3
"""event-ops の実行境界（Sandbox）と承認ゲート（Human Gate）。spec 002。

Claude Code の PreToolUse hook として、道具を呼ぶ直前に毎回動く。
- 禁止（支払い・契約・中止）……いつも止める（exit 2）
- 承認が要る（送信・公開・一斉メッセージ・招待・共有）……有効な承認が無ければ止める
- 送った版の URL への上書きの公開……止める（相手が見た版を変えない）
- 承認ファイル（approvals/）を AI が直接書く……止める（書けるのは人が端末で動かす approve.py だけ）
- それ以外（読む・下書きを作る）……通す

使う側のリポに loop/marketing/event-ops/ が無いときは何もしない（ほかの仕事を邪魔しない）。
止めたときは loop/marketing/event-ops/runs.jsonl に1行書く（実名・宛先は書かない）。
外部のライブラリは使わない（Python 3 の標準だけ）。
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("loop") / "marketing" / "event-ops"

# 既定の分け方。使う側の config.json の pay_tools / send_tools / allow_tools で足せる。
PAY_PATTERN = re.compile(r"(pay|payment|charge|checkout|purchase|refund|billing|subscribe|contract|envelope|sign_document|cancel_event|delete_event)", re.I)
SEND_PATTERN = re.compile(r"(send|reply|forward|blast|publish|invite|share|post_message|schedule_message|broadcast)", re.I)
DRAFT_PATTERN = re.compile(r"(draft)", re.I)
# 読むだけの道具（動詞が先頭）。送信の語が名前に入っていても通す
READ_PREFIX = re.compile(r"^(get|list|search|read|query|fetch|download|view|describe|discover|find|count|check)_", re.I)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_PATTERN = re.compile(r"https?://[^\s\"'<>）)]+")
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
BASH_WRITE_HINT = re.compile(r"(>|\btee\b|\bcp\b|\bmv\b|\brm\b|\btouch\b|\bmkdir\b|sed\s+-i|\bpython\d?\b|\bnode\b|\bperl\b|\bruby\b|\bdd\b|\binstall\b)")


def project_dir(payload):
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def strings_in(obj):
    """tool_input の中の文字列をすべて取り出す。"""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings_in(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from strings_in(v)


def short_name(tool_name):
    """mcp__server__send_message → send_message"""
    return tool_name.split("__")[-1]


def record(base, primitive, result, tool_name, fail_code, approval_id=None):
    line = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "layer": "middle",
        "primitive": primitive,
        "tool": tool_name,
        "result": result,
        "fail_code": fail_code,
    }
    if approval_id:
        line["approval"] = approval_id
    try:
        with open(base / "runs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass


def block(base, tool_name, fail_code, message):
    record(base, "sandbox", "blocked", tool_name, fail_code)
    sys.stderr.write(f"[event-ops 実行境界] {message}（{fail_code}）\n")
    sys.exit(2)


def read_names(base):
    """names.local（git に入れない）：番号<TAB>名前<TAB>メール"""
    table = {}
    f = base / "names.local"
    if not f.exists():
        return table
    for raw in f.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cols = raw.split("\t")
        pid = cols[0].strip()
        email = cols[2].strip().lower() if len(cols) > 2 else ""
        table[pid] = email
    return table


def sent_records(base):
    out = []
    for f in base.glob("events/*/sent/*.json"):
        d = load_json(f)
        if isinstance(d, dict) and d.get("url"):
            out.append(d)
    return out


def approvals(base):
    out = []
    for f in sorted(base.glob("events/*/approvals/A-*.json")):
        d = load_json(f)
        if isinstance(d, dict):
            out.append(d)
    return out


def is_live(approval, now):
    try:
        exp = datetime.fromisoformat(approval.get("expires_at", ""))
    except ValueError:
        return False
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp > now


def classify(tool_name, tool_input, config):
    name = short_name(tool_name)
    if tool_name in config.get("allow_tools", []) or name in config.get("allow_tools", []):
        return "allow"
    if tool_name in config.get("pay_tools", []) or name in config.get("pay_tools", []) or PAY_PATTERN.search(name):
        return "pay"
    if tool_name in config.get("send_tools", []) or name in config.get("send_tools", []):
        return "send"
    if READ_PREFIX.search(name):
        return "allow"
    if SEND_PATTERN.search(name) and not (DRAFT_PATTERN.search(name) and not re.search(r"send", name, re.I)):
        return "send"
    # 名前に出ない公開：visibility を public にする更新
    vis = tool_input.get("visibility") if isinstance(tool_input, dict) else None
    if isinstance(vis, str) and vis.lower() == "public":
        return "send"
    return "allow"


def check_approval_write(base, tool_name, tool_input):
    """承認ファイルは人だけが書く。AI の書き込みを止める。"""
    if tool_name in WRITE_TOOLS:
        path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        if "/approvals/" in path.replace("\\", "/"):
            block(base, tool_name, "approval_write", "承認ファイルは、人が自分の端末で approve.py を動かして作ります。AI は書けません")
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", ""))
        # approve.py は承認ファイルのパス（approvals/）を引数に取らないので、見逃しの例外は作らない
        if "approvals/" in cmd and BASH_WRITE_HINT.search(cmd):
            block(base, tool_name, "approval_write", "承認ファイルを書き換えるコマンドは止めます。承認は人が approve.py で行います")


def check_frozen_overwrite(base, tool_name, tool_input):
    """送った版の URL に上書きで公開しない。"""
    if short_name(tool_name) != "Artifact" or not isinstance(tool_input, dict):
        return
    action = (tool_input.get("action") or "publish").lower()
    url = tool_input.get("url")
    if action != "publish" or not url:
        return
    if tool_input.get("asset"):
        return
    sent_urls = {r["url"].rstrip("/") for r in sent_records(base)}
    if url.rstrip("/") in sent_urls:
        block(base, tool_name, "frozen_overwrite", "この URL は相手に送った凍結した版です。上書きせず、新しい版を別の URL で作ってください")


def is_publish(tool_name, tool_input):
    vis = tool_input.get("visibility") if isinstance(tool_input, dict) else None
    return bool(re.search(r"publish", short_name(tool_name), re.I)) or (isinstance(vis, str) and vis.lower() == "public")


def check_lines_sealed(base, tool_name, tool_input):
    """告知の公開は、目標の線を封じてから（spec 008）。開いているイベントのどれも封じていなければ止める。"""
    if not is_publish(tool_name, tool_input):
        return
    open_states = [load_json(f) or {} for f in base.glob("events/*/state.json")]
    open_states = [s for s in open_states if not s.get("closed")]
    if open_states and not any(s.get("lines_sealed") for s in open_states):
        block(base, tool_name, "lines_not_sealed", "告知の公開の前に、目標の線を封じてください（judge_lines.py seal）")


def check_send(base, tool_name, tool_input):
    check_lines_sealed(base, tool_name, tool_input)
    names = read_names(base)
    email_to_pid = {v: k for k, v in names.items() if v}
    texts = list(strings_in(tool_input))
    emails = {e.lower() for t in texts for e in EMAIL_PATTERN.findall(t)}
    urls = {u.rstrip("/") for t in texts for u in URL_PATTERN.findall(t)}
    sent = {r["url"].rstrip("/"): r.get("sha256") for r in sent_records(base)}
    name = short_name(tool_name)
    now = datetime.now(timezone.utc)

    reasons = []
    for a in approvals(base):
        tools = a.get("tools") or []
        if name not in tools and tool_name not in tools:
            reasons.append(f"{a.get('id')}: この道具は承認に入っていない")
            continue
        if not is_live(a, now):
            reasons.append(f"{a.get('id')}: 期限切れ")
            continue
        allowed = {email_to_pid.get(e) for e in emails}
        approved_to = set(a.get("to") or [])
        if None in allowed:
            reasons.append(f"{a.get('id')}: 宛先に、番号の分からない相手がいる")
            continue
        if not allowed <= approved_to:
            extra = sorted(allowed - approved_to)
            reasons.append(f"{a.get('id')}: 承認にない宛先 {', '.join(extra)}")
            continue
        kit = a.get("kit") or {}
        kit_url = (kit.get("url") or "").rstrip("/")
        bad_version = False
        for u in urls & set(sent):
            if u != kit_url or sent[u] != kit.get("sha256"):
                bad_version = True
        if kit_url in sent and sent[kit_url] != kit.get("sha256"):
            bad_version = True
        if bad_version:
            reasons.append(f"{a.get('id')}: 承認した版と、凍結した版のハッシュが違う")
            continue
        record(base, "human_gate", "allowed", tool_name, None, a.get("id"))
        return
    detail = "／".join(reasons) if reasons else "承認がひとつも無い"
    if any("宛先" in r for r in reasons):
        code = "unapproved_recipient"
    elif any("版" in r for r in reasons):
        code = "kit_mismatch"
    else:
        code = "no_approval"
    block(base, tool_name, code, f"送信・公開には、人のまとめ承認が要ります。{detail}")


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    base = project_dir(payload) / DATA_DIR
    if not base.is_dir():
        return 0  # event-ops を使っていないリポでは何もしない
    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    config = load_json(base / "config.json") or {}

    check_approval_write(base, tool_name, tool_input)
    check_frozen_overwrite(base, tool_name, tool_input)

    kind = classify(tool_name, tool_input, config)
    if kind == "pay":
        block(base, tool_name, "forbidden", "支払い・契約・中止の道具は禁止です（G2 は人が行います）")
    if kind == "send":
        check_send(base, tool_name, tool_input)
    return 0


if __name__ == "__main__":
    sys.exit(main())
