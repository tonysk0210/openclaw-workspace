#!/usr/bin/env python3
"""
根據分析結果，生成視頻創作 Prompt
支援：
  - 分析結果自動生成
  - 單支視頻資料生成
  - 使用 Claude API 增強 Prompt 品質（可選）
"""

import json
import os
import argparse
import glob
from datetime import datetime

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'prompts')


PROMPT_TEMPLATE = """
## 視頻創作 Prompt #{index}

**參考來源：** {platform} | 觀看：{views:,} | 點讚：{likes:,}
**原始標題：** {title}

---

### 📋 視頻概念
{concept}

### 🎬 場景設定
{scene}

### 👗 造型建議
{outfit}

### 🎭 動作與表現
{actions}

### 🎵 音樂氛圍
{music_vibe}

### 🏷️ 推薦 Hashtags
{hashtags}

### 📐 拍攝技巧
{shooting_tips}

---
"""


def infer_concept(video):
    title = video.get('title', '')
    actions = video.get('actions', '')
    scene = video.get('scene_description', '')

    if any(k in title.lower() for k in ['dance', '跳舞', '舞蹈']):
        return "舞蹈展示：展現舞技與魅力，節奏感強，適合跟拍熱門舞步"
    elif any(k in title.lower() for k in ['outfit', 'ootd', '穿搭', '換裝']):
        return "穿搭展示：快速換裝或日常穿搭分享，強調搭配美感與個人風格"
    elif any(k in title.lower() for k in ['vlog', '日常', 'daily', 'routine']):
        return "日常生活記錄：分享生活片段，展現自然真實的一面，增加親近感"
    elif any(k in title.lower() for k in ['makeup', '妝容', '化妝']):
        return "妝容教學或展示：前後對比或化妝過程，突出精緻感"
    elif any(k in title.lower() for k in ['travel', '旅遊', '出遊']):
        return "旅遊Vlog：外景拍攝，場景豐富，搭配美景增加視覺吸引力"
    else:
        return "生活美學內容：展現日常生活中的美感與個人特質，自然有魅力"


def infer_scene(video):
    scene = video.get('scene_description', '')
    if scene:
        return scene
    title = video.get('title', '').lower()
    if any(k in title for k in ['室內', 'indoor', '房間', 'home']):
        return "室內拍攝：整潔美觀的房間或臥室，自然光或暖色燈光，背景乾淨不雜亂"
    elif any(k in title for k in ['戶外', 'outdoor', '街拍', 'street']):
        return "戶外街拍：城市街景或咖啡廳外，自然光線，傍晚黃金時段效果最佳"
    else:
        return "選擇乾淨簡約的背景，室內柔和燈光或戶外自然光，避免雜亂元素干擾主體"


def infer_outfit(video):
    outfit = video.get('outfit', '')
    if outfit:
        return outfit
    return "依場景選擇：\n- 日常：休閒但精緻的穿搭，展現親和力\n- 正式：時尚感強的造型，突出個人品味\n- 運動：活力感穿搭，搭配動感動作"


def infer_actions(video):
    actions = video.get('actions', '')
    if actions:
        return actions
    return "自然流暢的動作，避免生硬。可包含：走路入鏡、轉身、整理頭髮、微笑看鏡頭等自然動作"


def infer_music_vibe(video):
    music = video.get('music', '')
    views = video.get('views', 0)
    if music:
        return f"推薦使用：{music}\n或選擇類似風格：節奏明快、流行感強的背景音樂"
    if views > 1000000:
        return "選用當前熱門 BGM / Trending Sound，增加被推薦演算法收錄的機率"
    return "選用輕快、積極的背景音樂，與視頻氛圍相符"


def infer_shooting_tips(video):
    platform = video.get('platform', '')
    tips = []
    if platform == 'tiktok':
        tips.append("豎屏 9:16 格式，全屏呈現")
        tips.append("前 1-3 秒必須抓住眼球（Hook），避免被滑走")
        tips.append("使用 TikTok 原生功能：特效、貼紙、文字疊加")
    elif platform == 'instagram':
        tips.append("Reels 豎屏 9:16，也可方形 1:1")
        tips.append("封面圖要精緻，符合整體 Feed 美學風格")
        tips.append("前 3 秒加入視覺亮點或文字鉤子")
    elif platform == 'youtube':
        tips.append("YouTube Shorts 豎屏 9:16，時長 60 秒內")
        tips.append("加入字幕增加可及性，尤其無聲觀看時")
    else:
        tips.append("豎屏 9:16 格式，適配所有短視頻平台")

    tips.extend([
        "保持穩定畫面，考慮使用三腳架或穩定器",
        "確保充足光線，自然光優於人工光",
        "多拍幾個 Take，剪輯時選最自然流暢的片段"
    ])
    return "\n".join(f"- {t}" for t in tips)


def generate_hashtags(video, top_tags):
    tags = video.get('tags', []) or video.get('hashtags', [])
    result_tags = list(tags[:5])

    common_tags = ['#shorts', '#viral', '#fyp', '#美女', '#trending']
    for t in common_tags:
        if t not in result_tags:
            result_tags.append(t)

    for tag, _ in top_tags[:5]:
        h = f"#{tag}"
        if h not in result_tags:
            result_tags.append(h)

    return ' '.join(result_tags[:15])


def generate_prompts_from_analysis(analysis_file):
    with open(analysis_file, encoding='utf-8') as f:
        data = json.load(f)

    top_videos = data.get('top_20_videos', [])
    top_tags = data.get('top_tags', [])

    prompts = []
    for i, video in enumerate(top_videos, 1):
        prompt = PROMPT_TEMPLATE.format(
            index=i,
            platform=video.get('platform', 'unknown').upper(),
            views=video.get('views', 0),
            likes=video.get('likes', 0),
            title=video.get('title', '（無標題）'),
            concept=infer_concept(video),
            scene=infer_scene(video),
            outfit=infer_outfit(video),
            actions=infer_actions(video),
            music_vibe=infer_music_vibe(video),
            hashtags=generate_hashtags(video, top_tags),
            shooting_tips=infer_shooting_tips(video)
        )
        prompts.append(prompt)

    return prompts, data


def main():
    parser = argparse.ArgumentParser(description='生成視頻創作 Prompt')
    parser.add_argument('--analysis', default=None, help='指定分析結果 JSON（不指定則使用最新）')
    parser.add_argument('--output', default=OUTPUT_DIR, help='輸出資料夾')
    args = parser.parse_args()

    if args.analysis:
        analysis_file = args.analysis
    else:
        files = sorted(glob.glob(os.path.join(PROCESSED_DIR, 'analysis_*.json')), reverse=True)
        if not files:
            print("找不到分析結果，請先執行 analyze.py")
            return
        analysis_file = files[0]

    print(f"使用分析結果: {analysis_file}")
    prompts, data = generate_prompts_from_analysis(analysis_file)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(args.output, f"prompts_{timestamp}.md")

    header = f"""# 美女短視頻創作 Prompts

生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}
分析視頻數：{data.get('total_videos', 0)}
平均互動率：{data.get('avg_engagement_rate', 0)}%

---

"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(prompts))

    print(f"已生成 {len(prompts)} 個 Prompt")
    print(f"輸出至: {output_file}")


if __name__ == '__main__':
    main()
