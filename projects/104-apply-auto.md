---
name: 104 全自動應徵
slug: 104-apply-auto
status: planned
started: 2026-06-02
owner: Clawton
tags: [104, apply, automation, java, jobs]
description: 自動搜尋 Java 職缺並依條件篩選後直接執行應徵
---

## 目標
搜尋符合條件的職缺 → 自動按「應徵」→ 回報應徵結果。

## 腳本（待建）
- `scripts/apply_104_auto.mjs`

## 待確認需求
- [ ] 篩選條件（地點、薪資下限、排除派遣等）
- [ ] 每次應徵上限（防止被 104 標記）
- [ ] 應徵後自附什麼自傳/附件？
- [ ] 重複應徵防呆（已投過的不重投）

## 注意
應徵是不可逆操作，需有防呆機制。
