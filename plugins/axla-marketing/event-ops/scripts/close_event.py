#!/usr/bin/env python3
"""中間ループの終わり（終了条件）と、外側の起動トリガー。spec 007。

イベントを閉じる3つの条件
  1. 撤収の確認：run-sheet.md の「撤収の確認」の箱が全部 [x]
  2. 精算：損益を記録した
  3. お礼の送信：来場者へのお礼を、人が送った
3つがそろったら state.json の closed を true にし、runs.jsonl に closed を書く（外側の review-event が起きる合図）。

使い方（どれも --event <フォルダ>）
  status                 # そろっていない条件を出す。そろっていなければ exit 1
  teardown               # 撤収の確認の箱が全部 [x] なら記録する
  settle --profit 32400  # 精算の損益（数字だけ）
  thanks-draft           # 来場者（checked_in）だけに送るお礼の下書き kit/thanks.json を作る（送るのは人）
  thanks-sent            # 人がお礼を送ったことを記録する
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

CONDITIONS = [("teardown_done", "撤収の確認"), ("settled", "精算"), ("thanks_sent", "お礼の送信")]


def teardown_boxes(event):
    rs = event / "run-sheet.md"
    if not rs.exists():
        return None
    lines = rs.read_text(encoding="utf-8").splitlines()
    inside, boxes = False, []
    for l in lines:
        if l.startswith("## "):
            inside = "撤収の確認" in l
            continue
        if inside:
            m = re.match(r"\s*- \[( |x|X)\]", l)
            if m:
                boxes.append(m.group(1).lower() == "x")
    return boxes


def set_register(base, event_id, **kw):
    f = base / "register.csv"
    with open(f, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields, rows = reader.fieldnames, list(reader)
    for r in rows:
        if r["id"] == event_id:
            r.update({k: str(v) for k, v in kw.items()})
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def maybe_close(event, st):
    if all(st.get(k) for k, _ in CONDITIONS) and not st.get("closed"):
        st["closed"] = True
        st["closed_at"] = lib.now_iso()
        st["stage"] = "outer"
        lib.save_json(event / "state.json", st)
        base = lib.base_of_event(event)
        set_register(base, event.name, state="closed")
        lib.append_to_section(event / "event-log.md", "いまの状態と次の一手", f"- {lib.now_iso()[:10]} 終了（撤収・精算・お礼がそろった）。次：review-event で学びをまとめる")
        lib.record_run(base, "middle", "exit_criteria", "closed", None, event=event.name)
        print("イベントを閉じました。次は review-event（外側のループ）")


def main():
    p = argparse.ArgumentParser(description="中間ループの終わり")
    p.add_argument("cmd", choices=["status", "teardown", "settle", "thanks-draft", "thanks-sent"])
    p.add_argument("--event", required=True)
    p.add_argument("--profit", type=int)
    a = p.parse_args()
    event = Path(a.event)
    st = lib.load_json(event / "state.json", {})

    if a.cmd == "status":
        missing = [label for k, label in CONDITIONS if not st.get(k)]
        if missing:
            print("閉じるのに足りないもの：" + "、".join(missing))
            return 1
        print("3つともそろっています" + ("（終了済み）" if st.get("closed") else ""))
        return 0

    if a.cmd == "teardown":
        boxes = teardown_boxes(event)
        if not boxes:
            print("run-sheet.md に「撤収の確認」の箱がありません")
            return 1
        if not all(boxes):
            print(f"撤収の確認が {boxes.count(False)} 件残っています")
            return 1
        st["teardown_done"] = True
        lib.save_json(event / "state.json", st)
        lib.append_to_section(event / "event-log.md", "当日の記録", f"- {lib.now_iso()[:10]} 撤収の確認がすべて済んだ")
        print("撤収の確認を記録しました")

    elif a.cmd == "settle":
        if a.profit is None:
            p.error("--profit に損益（数字）を入れてください")
        st["settled"] = True
        st["profit"] = a.profit
        lib.save_json(event / "state.json", st)
        set_register(lib.base_of_event(event), event.name, profit=a.profit)
        lib.append_to_section(event / "event-log.md", "当日の記録", f"- {lib.now_iso()[:10]} 精算：損益 {a.profit:,}")
        print("精算を記録しました")

    elif a.cmd == "thanks-draft":
        tmpl = Path(__file__).resolve().parent.parent / "templates" / "thanks.md"
        user = lib.base_of_event(event) / "templates" / "thanks.md"
        text = (user if user.exists() else tmpl).read_text(encoding="utf-8")
        lib.save_json(event / "kit" / "thanks.json", {"recipient_groups": ["checked_in"], "message_md": text, "visibility": "draft"})
        print("お礼の下書きを kit/thanks.json に作りました。送り先は来場者（checked_in）だけ。送る前に、来場の件数と受付の実数を人が見比べてください")
        return 0

    elif a.cmd == "thanks-sent":
        st["thanks_sent"] = True
        lib.save_json(event / "state.json", st)
        lib.append_to_section(event / "event-log.md", "当日の記録", f"- {lib.now_iso()[:10]} 来場者にお礼を送った（送ったのは人）")
        print("お礼の送信を記録しました")

    maybe_close(event, lib.load_json(event / "state.json", {}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
