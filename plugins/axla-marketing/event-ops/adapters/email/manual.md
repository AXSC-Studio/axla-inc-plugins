# ~~email = manual（人が知らせる）

見張りをつながないときは、人が「送った」「返事が来た」を入れる。

```bash
python3 scripts/update_partners.py sent    --partner PT-002 --event <フォルダ>
python3 scripts/update_partners.py replied --partner PT-002 --event <フォルダ>
python3 scripts/update_partners.py offline --partner PT-001 --note "電話で決まったこと" --event <フォルダ>
```

返事の中身は、メールを貼るか、coordinate-partners に「PT-002 から返事が来た」と頼む。
