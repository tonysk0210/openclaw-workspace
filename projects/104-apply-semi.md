---
name: 104 半自動應徵
slug: 104-apply-semi
status: active
started: 2026-06-02
owner: Clawton
tags: [104, apply, semi-auto, java, jobs]
description: 搜尋職缺後傳清單給 Tony 確認，等批准才執行應徵
---

## 腳本
- `scripts/search_104_semi.mjs` — Step 1：搜尋、過濾已投、存 pending list
- `scripts/apply_104_semi.mjs` — Step 2：對指定號碼執行 CDP 應徵
- `data/pending_jobs.json` — 當次搜尋暫存
- `data/apply_log.json` — 累積投遞紀錄（防重複）

## 使用流程
1. 我執行搜尋，傳清單給 Tony
2. Tony 回覆「投 2 5 8」
3. 我執行應徵並回報結果

## 確認需求
- 地區：不限
- 求職信：使用 104 帳號預設
- 每批：10 筆
- 已投職缺：自動過濾，不重複投
