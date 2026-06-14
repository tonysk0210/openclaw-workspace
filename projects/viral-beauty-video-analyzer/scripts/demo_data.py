"""
Demo 資料：模擬各平台熱門美女短視頻資料
供 generate_ai_video_prompt.py --demo 使用
"""

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
        "actions": "起床伸展，喝水，護膚，換裝，出門，每個動作轉場流暢"
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
        "actions": "走路入鏡，轉身 360 展示穿搭，自信微笑看鏡頭"
    },
    {
        "platform": "youtube",
        "title": "Dance Challenge 2025 | 挑戰最新神曲舞步",
        "views": 5200000,
        "likes": 420000,
        "hashtags": ["#dancechallenge", "#shorts", "#viral", "#舞蹈", "#trending"],
        "music": "APT. - ROSE & Bruno Mars",
        "duration_sec": 30,
        "scene_description": "室內，白牆背景，環形燈補光，乾淨極簡風格",
        "outfit": "螢光色運動上衣 + 黑色緊身褲，活力感十足",
        "actions": "完整跳完當前最熱舞步，節奏精準，表情帶感情"
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
        "actions": "進入咖啡廳，點餐，翻書閱讀，喝咖啡特寫，窗外望向遠方"
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
        "actions": "慢步走在街道，回頭看鏡頭，燈光在背景中閃爍，慢動作片段"
    },
    {
        "platform": "instagram",
        "title": "Beach Day 🌊 Summer Vibes",
        "views": 4200000,
        "likes": 360000,
        "hashtags": ["#beach", "#summer", "#beachday", "#summervibe", "#aesthetic"],
        "music": "Cruel Summer - Taylor Swift",
        "duration_sec": 35,
        "scene_description": "晴天沙灘，碧藍海水，白色沙灘，陽光充足，棕櫚樹背景",
        "outfit": "白色蕾絲連衣裙，草編帽，沙灘造型",
        "actions": "在沙灘上漫步，玩水，坐在沙灘上看海，頭髮隨風飄動"
    },
    {
        "platform": "tiktok",
        "title": "Glow Up 發光系妝容教學 ✨",
        "views": 6800000,
        "likes": 520000,
        "hashtags": ["#glowup", "#makeup", "#makeuptutorial", "#妝容", "#美妝"],
        "music": "Flowers - Miley Cyrus",
        "duration_sec": 60,
        "scene_description": "乾淨明亮的化妝台，環形燈，鏡子，各種化妝品擺放整齊",
        "outfit": "白色浴袍，護膚狀態，自然素顏到精緻妝容前後對比",
        "actions": "素顏狀態，打底，上妝，腮紅，口紅，完成回頭一笑"
    }
]

TOP_TAGS = [
    ("fyp", 45), ("viral", 38), ("shorts", 35), ("美女", 30),
    ("trending", 28), ("lifestyle", 22), ("aesthetic", 20),
    ("ootd", 18), ("vlog", 15), ("日常", 12)
]
