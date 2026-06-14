#!/usr/bin/env python3
"""
手動匯入其他平台（TikTok / IG / FB / X）視頻資料
複製 data/raw/manual_template.json 並填入視頻資訊後執行
"""

import json
import os
import argparse
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')


def validate_entry(entry):
    required = ['platform', 'url', 'views', 'likes']
    for field in required:
        if field not in entry:
            return False, f"缺少欄位: {field}"
    if entry['views'] == 0:
        return False, "觀看數不能為 0"
    return True, None


def main():
    parser = argparse.ArgumentParser(description='手動匯入視頻資料')
    parser.add_argument('--input', required=True, help='輸入 JSON 檔案路徑')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"檔案不存在: {args.input}")
        return

    with open(args.input, encoding='utf-8') as f:
        entries = json.load(f)

    valid = []
    for i, entry in enumerate(entries):
        ok, err = validate_entry(entry)
        if ok:
            entry['fetched_at'] = datetime.now().isoformat()
            entry['source'] = 'manual'
            valid.append(entry)
        else:
            print(f"  跳過第 {i+1} 筆: {err}")

    print(f"匯入 {len(valid)}/{len(entries)} 筆有效資料")

    output_file = os.path.join(OUTPUT_DIR, f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(valid, f, ensure_ascii=False, indent=2)

    print(f"已儲存至: {output_file}")


if __name__ == '__main__':
    main()
