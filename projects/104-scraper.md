---
name: 104 職缺搜尋爬蟲
slug: 104-scraper
status: active
started: 2026-06-02
owner: Clawton
tags: [104, scraper, java, jobs]
description: 搜尋 104 Java 職缺並輸出 CSV 報表，每次獨立批次執行
---

## 目標
從 104 人力銀行搜尋 Java 職缺，抓取完整職缺資訊，輸出 CSV 到桌面。

## 腳本
- 主腳本：`scripts/scrape_104_cdp.mjs`
- 執行腳本：`/tmp/run_extra.sh`
- 桌面備份：`~/Desktop/scrape_104_cdp.mjs`

## CSV 欄位（定版）
`# | 職缺名稱 | 公司名稱 | 薪資待遇 | 工作地點 | 工作內容 | 條件要求 | 連結`

## 執行規則
- 每次獨立批次，不合併前次結果
- 預設 **10 筆**測試，Tony 確認後再調整筆數
- 排序：符合度高（order=14）、最近更新（order=1）各產一份

## 進度
- [x] CDP 瀏覽器自動化
- [x] 工作內容完整抓取
- [x] 條件要求結構化抓取（工作經歷/學歷/科系/擅長工具/其他條件）
- [x] 公司名稱獨立欄位
- [ ] 後續微調（Tony 主導）
