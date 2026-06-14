---
name: 104-java-scraper
description: 104 Java 職缺爬蟲工作流：腳本路徑、欄位定義、執行方式、注意事項
metadata:
  type: project
---

## 腳本位置
- 主腳本：`scripts/scrape_104_cdp.mjs`（Node.js，直接連 Chrome CDP）
- 執行腳本：`/tmp/run_extra.sh`（nohup 背景跑，循序執行）

## 執行方式（每次獨立批次，固定 10 筆）

```bash
# 準備 URL 清單（從搜尋結果頁抓，含公司名稱）
# 符合度高 URL → /tmp/extra_rel.json
# 最近更新 URL → /tmp/extra_rec.json

nohup /tmp/run_extra.sh > /tmp/extra_main.log 2>&1 &
# 完成後輸出到 /tmp/extra_done.txt (最後一行 "ALL DONE")
```

## CSV 欄位（最終確認版）
`# | 職缺名稱 | 公司名稱 | 薪資待遇 | 工作地點 | 工作內容 | 條件要求 | 連結`

## 條件要求抓法
掃 DOM 找 `工作經歷/學歷要求/科系要求/語文條件/擅長工具/工作技能/其他條件` 的 label，
抓相鄰 sibling 的 innerText，排除「不拘」，用 ` | ` 連接。

## 關鍵設計決策
- **每次獨立批次**，不合併舊資料
- **固定 10 筆**，Tony 確認格式後再決定放大筆數
- **nohup + 循序**：避免進程被 OpenClaw 180s watchdog 砍掉 + 避免多進程搶同一 Chrome tab

## 搜尋排序參數
- 符合度高：`order=14`
- 最近更新：`order=1`

**Why:** 2026-06-02 調校完成，Tony 確認格式 OK。
**How to apply:** 下次執行前先確認 Chrome 已開且已登入 104。
