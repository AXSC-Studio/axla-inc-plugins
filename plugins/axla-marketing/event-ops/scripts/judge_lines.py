#!/usr/bin/env python3
"""目標の線を封じ、結果と照らす（外側のループの検証器）。spec 008。

seal  … lines.json の線のハッシュを register.csv（git に入る）に刻む。告知の公開の前に行う
        （spec 002 の hook は、線を封じていないと告知の公開を止める）
judge … 封じた線と結果（register.csv の件数、または --results の外の結果）を照らし、
        線ごとに 当たり／弱い当たり／外れ を出す。線が封じたときと違えば exit 2（書き換えを許さない）
        人の判断の数（承認の数＋G1 の数）を前回のイベントと比べる
        同じ fail_code が2回以上なら、EVENTS.md に上げる案として learning-pr.md に書く

使い方
  python3 judge_lines.py seal  --event <フォルダ>
  python3 judge_lines.py judge --event <フォルダ> [--results <外の結果の JSON {"metric": 値}>]
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

# よく出る失敗に、決まりの案を添える（ない失敗は「どう防ぐかを書く」とだけ出す）
SUGGEST = {
    "unapproved_recipient": "宛先を足すときは新しいまとめ承認を作る、を EVENTS.md の手順に書く",
    "kit_mismatch": "資料を直したら freeze_kit.py で新しい版を凍結してから承認する、を手順に書く",
    "no_approval": "送る前に approve.py のまとめ承認を取る、を手順の先頭に書く",
    "frozen_overwrite": "送った資料は版を上げて新しい URL で作る、を手順に書く",
    "approval_write": "承認は人が端末で approve.py を動かす、を手順に書く",
    "max_rounds": "内側が3周で終わらなかった項目の既定値を、EVENTS.md の既定値表に足す",
    "reply_wait": "返事待ちの日数と催促の雛形を、相手の種類ごとに EVENTS.md に書く",
    "plan_changed": "条件が変わりやすい項目（料金・時間）は、確定まで【仮】で出す、を既定値に書く",
    "bad_evidence": "証拠のファイルの置き場所（kit/・evidence/）を手順に書く",
}


def lines_hash(lines):
    body = json.dumps(lines.get("lines", []), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def count_judgments(event):
    approvals = len(list((event / "approvals").glob("*.json"))) if (event / "approvals").is_dir() else 0
    g1 = 0
    log = event / "event-log.md"
    if log.exists():
        inside = False
        for l in log.read_text(encoding="utf-8").splitlines():
            if l.startswith("## "):
                inside = "開いている人の判断" in l
                continue
            if inside and l.strip().startswith("- ") and "G1" in l:
                g1 += 1
    return approvals + g1


def fail_codes(base, event_id, created):
    out = Counter()
    f = base / "runs.jsonl"
    if not f.exists():
        return out
    for raw in f.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(raw)
        except ValueError:
            continue
        if not r.get("fail_code"):
            continue
        if r.get("event") == event_id or (not r.get("event") and created and r.get("ts", "")[:10] >= created):
            out[r["fail_code"]] += 1
    return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cmd_seal(event):
    base = lib.base_of_event(event)
    lines = lib.load_json(event / "lines.json")
    if not lines or not lines.get("lines") or not all("metric" in x and "target" in x for x in lines["lines"]):
        print("lines.json に、metric と target のある線が要ります")
        return 1
    h = lines_hash(lines)
    lib.set_register(base, event.name, lines_sha256=h)
    st = lib.load_json(event / "state.json", {})
    st["lines_sealed"], st["lines_sha256"], st["lines_sealed_at"] = True, h, lib.now_iso()
    lib.save_json(event / "state.json", st)
    lib.append_to_section(event / "event-log.md", "既定値で決めたこと", f"- {lib.now_iso()[:10]} 目標の線を封じた（{len(lines['lines'])} 本。ハッシュ {h[:12]}… を register.csv に）")
    data = lib.load_checklist(event)
    for item in data.get("items", []):
        if item["id"] == "lines":
            item["passes"], item["evidence"] = True, "lines.json"
    lib.save_json(lib.checklist_path(event), data)
    lib.record_run(base, "outer", "verifier", "sealed", None, event=event.name)
    print(f"目標の線を封じました（{len(lines['lines'])} 本）。sha256: {h}")
    return 0


def cmd_judge(event, results_path):
    base = lib.base_of_event(event)
    fields, rows = lib.read_register(base)
    row = next((r for r in rows if r.get("id") == event.name), None)
    lines = lib.load_json(event / "lines.json")
    if row is None or not row.get("lines_sha256"):
        print("目標の線が封じられていません（judge_lines.py seal）。封じていない線では判定しません")
        return 2
    if not lines or lines_hash(lines) != row["lines_sha256"]:
        print("目標の線が、封じたあとに書き換えられています。判定しません（変えたいなら G1 に上げ、学びとして残す）")
        lib.record_run(base, "outer", "verifier", "blocked", "lines_rewritten", event=event.name)
        return 2
    results = lib.load_json(results_path, {}) if results_path else {}
    weak = float(lines.get("weak_ratio", lib.load_json(base / "config.json", {}).get("weak_ratio", 0.8)))
    table = ["| 線 | 目標 | 結果 | 判定 | 定義 |", "|---|---|---|---|---|"]
    misses = []
    for ln in lines["lines"]:
        actual = num(results.get(ln["metric"], row.get(ln["metric"])))
        target = num(ln["target"])
        if actual is None:
            verdict = "結果なし"
        elif actual >= target:
            verdict = "当たり"
        elif target > 0 and actual >= target * weak:
            verdict = "弱い当たり"
        else:
            verdict = "外れ"
        if verdict in ("外れ", "結果なし"):
            misses.append(ln["id"])
        shown = "—" if actual is None else f"{actual:g}"
        table.append(f"| {ln['id']} | {target:g} | {shown} | {verdict} | {ln.get('definition', '')} |")

    judgments = count_judgments(event)
    prev = None
    for r in rows:
        if r.get("id") == event.name:
            break
        if r.get("judgments"):
            prev = r
    lib.set_register(base, event.name, judgments=judgments)
    if prev:
        before = int(float(prev["judgments"]))
        diff = f"人の判断の数：{before} → {judgments}（前回 {prev['id']}）" + ("。減った" if judgments < before else "。**減らなかった**")
    else:
        diff = f"人の判断の数：{judgments}（比べる前回なし）"

    codes = fail_codes(base, event.name, row.get("created", ""))
    repeated = {c: n for c, n in codes.items() if n >= 2}
    review = ["# 振り返り：" + event.name, "", "## 線と結果", *table, "", "## 人の手", f"- {diff}", "",
              "## 失敗の数（runs.jsonl の fail_code）"]
    review += [f"- {c}：{n} 回" for c, n in codes.most_common()] or ["- なし"]
    (event / "review.md").write_text("\n".join(review) + "\n", encoding="utf-8")

    pr = ["# 学びの PR の案：" + event.name, "",
          "> review-event が作る下書き。人が読んで直し、使う側のリポで EVENTS.md と templates/ への PR にする（マージは人）。", "",
          "## EVENTS.md に足す案（同じ失敗が2回以上）"]
    pr += [f"- `{c}` が {n} 回：{SUGGEST.get(c, 'どう防ぐかを決まりに書く')}" for c, n in sorted(repeated.items())] or ["- なし"]
    pr += ["", "## 線の見直しの候補（次のイベントで）"]
    pr += [f"- `{m}`：外れ／結果なし。定義か目標を見直す（封じた線は今回のものは変えない）" for m in misses] or ["- なし"]
    if prev and judgments >= int(float(prev["judgments"])):
        pr += ["", "## なぜ人の判断が減らなかったか", "- （review-event がここに理由を書く）"]
    (event / "learning-pr.md").write_text("\n".join(pr) + "\n", encoding="utf-8")

    lib.append_to_section(event / "event-log.md", "学び", f"- {lib.now_iso()[:10]} 振り返り：review.md・learning-pr.md。{diff}")
    lib.record_run(base, "outer", "verifier", "reviewed", None, event=event.name, judgments=judgments, repeated=len(repeated))
    print("review.md と learning-pr.md を作りました。" + diff)
    return 0


def main():
    p = argparse.ArgumentParser(description="目標の線を封じ、結果と照らす")
    p.add_argument("cmd", choices=["seal", "judge"])
    p.add_argument("--event", required=True)
    p.add_argument("--results")
    a = p.parse_args()
    event = Path(a.event)
    return cmd_seal(event) if a.cmd == "seal" else cmd_judge(event, a.results)


if __name__ == "__main__":
    sys.exit(main())
