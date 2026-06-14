#!/usr/bin/env python3
"""
Demo：使用範例資料直接生成 Prompt，無需 API Key
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from generate_prompt import (
    infer_concept, infer_scene, infer_outfit,
    infer_actions, infer_music_vibe, infer_shooting_tips,
    generate_hashtags, PROMPT_TEMPLATE
)

DEMO_VIDEOS = [
    {
        "platform": "tiktok",
        "title": "晨間日常routine ☀️ 跟我一起開始元氣的一天",
        "views": 3800000,
        "likes": 280000,
        "hashtags": ["#morningroutine", "#日常", "#美女", "#lifestyle", "#fyp"],
        "music": "Aesthetic - Xilo",
        "duration_sec": 45,
        "scene_description": "明亮整潔的臥室，大窗自然光，白色床鋪，植物點綴",
        "outfit": "白色寬鬆oversize上衣 + 高腰短褲，清新自然感",
        "actions": "起床伸展 → 喝水 → 護膚 → 換裝 → 出門，每個動作轉場流暢",
        "url": "https://www.tiktok.com/@example/video/demo1"
    },
    {
        "platform": "instagram",
        "title": "OOTD Check ✨ Street Style in Taipei",
        "views": 1500000,
        "likes": 95000,
        "hashtags": ["#ootd", "#streetstyle", "#taipei", "#fashion", "#美女"],
        "music": "Golden Hour - JVKE",
        "duration_sec": 20,
        "scene_description": "台北街頭，傍晚黃金時段，復古建築背景，溫暖光線",
        "outfit": "棕色皮革外套 + 白色基本款上衣 + 寬褲，韓系時尚感",
        "actions": "走路入鏡，轉身 360 展示穿搭，自信微笑看鏡頭",
        "url": "https://www.instagram.com/reel/demo2"
    },
    {
        "platform": "youtube",
        "title": "Dance Challenge 2024 | 挑戰最新神曲舞步",
        "views": 5200000,
        "likes": 420000,
        "hashtags": ["#dancechallenge", "#shorts", "#viral", "#舞蹈", "#trending"],
        "music": "APT. - ROSE & Bruno Mars",
        "duration_sec": 30,
        "scene_description": "室內，白牆背景，環形燈補光，乾淨極簡風格",
        "outfit": "螢光色運動上衣 + 黑色緊身褲，活力感十足",
        "actions": "完整跳完當前最熱舞步，節奏精準，表情帶感情",
        "url": "https://www.youtube.com/shorts/demo3"
    },
    {
        "platform": "tiktok",
        "title": "咖啡廳vlog ☕ 在最美的地方讀書",
        "views": 2100000,
        "likes": 180000,
        "hashtags": ["#cafevlog", "#studyvlog", "#aesthetic", "#咖啡廳", "#日常"],
        "music": "Study With Me Lo-fi",
        "duration_sec": 60,
        "scene_description": "氛圍感咖啡廳，木質桌椅，窗邊位置，自然光，書本與咖啡入鏡",
        "outfit": "米色針織毛衣 + 格子長裙，知性文藝感",
        "actions": "進入咖啡廳 → 點餐 → 翻書閱讀 → 喝咖啡特寫 → 窗外望向遠方",
        "url": "https://www.tiktok.com/@example/video/demo4"
    },
    {
        "platform": "x",
        "title": "晚上散步記錄 🌙",
        "views": 890000,
        "likes": 62000,
        "hashtags": ["#nightwalk", "#nightlife", "#aesthetic", "#vlog"],
        "music": "Night Dancer - imase",
        "duration_sec": 25,
        "scene_description": "夜晚城市街道，霓虹燈光，行人稀少，夢幻氛圍",
        "outfit": "黑色長版風衣 + 白色內搭，夜晚感強烈",
        "actions": "慢步走在街道，回頭看鏡頭，燈光在背景中閃爍，慢動作片段",
        "url": "https://x.com/example/demo5"
    }
]

TOP_TAGS = [
    ("fyp", 45), ("viral", 38), ("shorts", 35), ("美女", 30),
    ("trending", 28), ("lifestyle", 22), ("aesthetic", 20),
    ("ootd", 18), ("vlog", 15), ("日常", 12)
]


def main():
    output_lines = [
        "# 美女短視頻創作 Prompt 範例\n",
        "（基於熱門視頻分析自動生成）\n",
        "---\n"
    ]

    for i, video in enumerate(DEMO_VIDEOS, 1):
        prompt = PROMPT_TEMPLATE.format(
            index=i,
            platform=video['platform'].upper(),
            views=video['views'],
            likes=video['likes'],
            title=video['title'],
            concept=infer_concept(video),
            scene=infer_scene(video),
            outfit=infer_outfit(video),
            actions=infer_actions(video),
            music_vibe=infer_music_vibe(video),
            hashtags=generate_hashtags(video, TOP_TAGS),
            shooting_tips=infer_shooting_tips(video)
        )
        output_lines.append(prompt)

    output_path = os.path.join(
        os.path.dirname(__file__), '..', 'output', 'prompts', 'demo_prompts.md'
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"Demo Prompt 已生成: {output_path}")
    return output_path


if __name__ == '__main__':
    main()
