# Viral Beauty Video Analyzer

從 TikTok、YouTube、Facebook、IG、X 等平台，找出高觀看、高點讚的美女短視頻，分析內容模式，生成可複製的視頻創作 Prompt。

## 功能

1. **資料收集**：透過各平台 API / 搜尋工具抓取熱門短視頻資訊
2. **內容分析**：分析視頻標題、標籤、描述、互動數據
3. **Prompt 生成**：根據分析結果生成對應的視頻創作 Prompt

## 資料夾結構

```
viral-beauty-video-analyzer/
├── README.md
├── config.json              # API 金鑰與設定
├── scripts/
│   ├── fetch_youtube.py     # YouTube Data API 抓取
│   ├── fetch_manual.py      # 手動匯入其他平台資料
│   ├── analyze.py           # 內容分析引擎
│   └── generate_prompt.py   # Prompt 生成器
├── data/
│   ├── raw/                 # 原始抓取資料
│   └── processed/           # 分析後結果
└── output/
    └── prompts/             # 生成的 Prompt 輸出
```

## 使用方式

### Step 1：設定 API 金鑰
編輯 `config.json`，填入 YouTube Data API Key。

### Step 2：抓取 YouTube 熱門視頻
```bash
python3 scripts/fetch_youtube.py --query "美女 shorts" --max-results 50
```

### Step 3：手動匯入其他平台資料（TikTok / IG / FB / X）
參考 `data/raw/manual_template.json`，手動填入視頻資訊後執行：
```bash
python3 scripts/fetch_manual.py --input data/raw/manual_input.json
```

### Step 4：分析內容
```bash
python3 scripts/analyze.py
```

### Step 5：生成 Prompt
```bash
python3 scripts/generate_prompt.py --output output/prompts/
```

## 平台限制說明

| 平台 | 方式 | 備註 |
|------|------|------|
| YouTube | 官方 Data API v3 | 需要 API Key（免費） |
| TikTok | 手動 / TikTok Research API | Research API 需申請 |
| Instagram | 手動匯入 | 官方 API 限制嚴格 |
| Facebook | 手動匯入 | 需 Meta 開發者帳號 |
| X (Twitter) | 手動 / X API v2 | 免費版有限制 |
