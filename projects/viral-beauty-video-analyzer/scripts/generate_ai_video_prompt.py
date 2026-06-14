#!/usr/bin/env python3
"""
AI 影片生成 Prompt 生成器 v3 — 內容 · 畫面 · 轉場 版
人物樣板由用戶自行設定，此腳本輸出：
  1. 內容腳本 — 概念 / 敘事弧 / 情緒走向
  2. 分鏡畫面 — 鏡頭清單 (角度 / 構圖 / 景別 / 焦距)
  3. 轉場方式 — 每個切點的具體轉場技術
適用：Sora · Runway Gen-3/4 · Kling AI · Pika Labs
"""

import json
import os
import argparse
import glob
from datetime import datetime

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'prompts')

# ─── Content type classifier ─────────────────────────────────────────────────

def classify(video: dict) -> str:
    t = (video.get('title', '') + ' ' + ' '.join(video.get('tags', []))).lower()
    if any(k in t for k in ['dance', 'dancing', 'shuffle', 'trending dance', 'military dance', 'challenge']):
        return 'dance'
    if any(k in t for k in ['makeup', 'beauty', 'lip', 'glow', 'skin', 'skincare', '化妝', '妝容']):
        return 'beauty'
    if any(k in t for k in ['pov', 'karma', 'sales', 'vip', 'customer', 'reveal', 'prom']):
        return 'drama_fashion'
    if any(k in t for k in ['ootd', 'outfit', 'fashion', 'dress', 'style', 'heels', 'accessories', 'inspo']):
        return 'fashion'
    if any(k in t for k in ['morning', 'routine', 'vlog', 'cafe', 'coffee', 'daily', '日常', '晨間']):
        return 'lifestyle'
    return 'lifestyle'


# ─── Content scripts ──────────────────────────────────────────────────────────

CONTENT_SCRIPTS = {

    'dance': {
        'concept_cn': '趨勢舞蹈展示——以高能量舞步帶動觀眾節奏感，前3秒用最強動作鉤子留住滑動的手指，中段完整呈現舞步，結尾定格或慢動作回眸收尾。',
        'concept_en': 'Viral dance showcase — hook viewers in the first 3 seconds with the most impactful move, deliver the full choreography in the mid-section, close with a freeze-frame or slow-motion look-back.',
        'shots': [
            ('S1 — 開場鉤子（0–2s）', 'Opening Hook', '全身廣角 / 低角度仰拍 35mm，主體佔畫面 70%，背景淺景深虛化——展示最吸引人的單個動作定格', 'Full body wide, low-angle upshot 35mm, subject fills 70% frame, shallow background bokeh — single most impressive move, freeze-frame opening'),
            ('S2 — 主體舞步（2–10s）', 'Main Choreography', '中景至全景切換，跟蹤拍攝隨舞步移動，鏡頭保持輕微動感（手持搖晃感）以增加代入感', 'Medium to full shot alternating, tracking camera follows choreography, slight handheld organic sway for immersion'),
            ('S3 — 特寫細節（隱藏在中段）', 'Detail Insert', '腰部以下或手部特寫，快速插入1秒，展示腳步 / 手臂隔離動作——增加視覺層次', 'Sub-waist or hand close-up, 1-second insert, showcasing footwork or arm isolation — adds visual depth'),
            ('S4 — 高潮節拍（8–12s）', 'Drop/Climax', '極低角度 (地面level)，鏡頭對準腳步或裙擺，120fps慢動作拍攝，配合音樂 Drop 或最強節拍', 'Ground-level extreme low angle on footwork or hem, 120fps slow-motion synced to music drop or peak beat'),
            ('S5 — 結尾定格（12–15s）', 'Ending Pose', '推進至中近景，主體靜止造型，輕微Rack Focus從背景拉至眼睛，持續1.5秒後淡出', 'Push to medium-close, subject holds pose, rack focus from background to eyes, hold 1.5s then fade'),
        ],
        'transitions': [
            ('S1→S2', '節拍切換（Hard Cut on Beat）', '在音樂鼓點落下的瞬間硬切，0幀過渡，視覺衝擊感最強', 'Hard cut precisely on drum beat hit, zero-frame transition, maximum visual impact'),
            ('S2→S3', '旋轉遮幕（Spin Wipe）', '主體旋轉動作帶動鏡頭，在旋轉最快的一幀切入特寫，利用動態模糊做天然遮幕', 'Subject spin motion drives cut — at the fastest rotation frame, cut into close-up using motion blur as natural wipe'),
            ('S3→S4', '閃白轉場（Flash Cut）', '插入2幀純白閃光後切入低角度慢動作，製造「時間膨脹」感', 'Insert 2 frames of pure white flash before cutting to low-angle slo-mo — creates "time dilation" effect'),
            ('S4→S5', '慢動作拖尾（Slow-Mo Tail）', '慢動作從120fps自然減速至靜止，不做硬切，直接在慢動作中凝固成最終造型', 'Slow-mo organically decelerates from 120fps to freeze — no hard cut, movement itself crystallizes into final pose'),
        ],
    },

    'fashion': {
        'concept_cn': 'OOTD 造型展示——快節奏換裝或單套造型全方位呈現，重點是每套造型都要有「wow moment」：一個讓人想截圖的瞬間。',
        'concept_en': 'OOTD showcase — rapid outfit transitions or single-look full reveal. Every look needs a "wow moment": one frame viewers will want to screenshot.',
        'shots': [
            ('S1 — 進場（0–2s）', 'Walk-In Entry', '鏡頭從腳部/下擺開始，緩慢上搖（Tilt Up）至全臉，時長1.5秒，建立期待感', 'Camera starts at feet/hem, slow tilt-up pan to full face over 1.5 seconds, building anticipation'),
            ('S2 — 全身展示（2–6s）', 'Full Look Reveal', '正面全景靜止鏡頭（Locked-off），主體從左走到右再回中，停留在中央做造型動作', 'Locked-off frontal wide shot, subject walks left-to-right then centers, executes signature pose'),
            ('S3 — 360° 旋轉（4–8s）', 'Spin Showcase', '鏡頭固定，主體自轉一圈，OR 鏡頭環繞主體做軌道拍攝——二選一', 'Camera fixed + subject full 360° spin OR camera orbits subject — choose one based on tool capability'),
            ('S4 — 服裝細節特寫（7–10s）', 'Detail Close-Ups', '快速切3個局部特寫：領口/袖口細節 → 腰部收腰效果 → 鞋款側面，每個1秒', 'Three quick detail cuts: neckline/cuff → waist cinch effect → shoe side profile, each 1 second'),
            ('S5 — 結尾眼神（11–15s）', 'Final Gaze', '推進至大特寫（眼部到下巴），主體直視鏡頭，輕揚嘴角或單挑眉，配合燈光高光', 'Push to extreme close-up (eyes to chin), subject stares directly at camera, subtle smirk or eyebrow raise, rim light highlight'),
        ],
        'transitions': [
            ('S1→S2', '上搖接靜鏡（Tilt-to-Lock）', '上搖到達全身時速度歸零，畫面自然凝固為靜止廣角，無需切點', 'Tilt naturally decelerates to zero as it reaches full-body frame — motion itself creates the static locked shot, no cut needed'),
            ('S2→S3', '甩髮遮幕（Hair Whip Wipe）', '主體甩頭帶動髮絲橫掃畫面，在髮絲遮滿整個畫面的一幀切入旋轉鏡頭', 'Subject hair whip sweeps across frame — at the frame where hair covers full screen, cut to spin shot (natural hair-wipe transition)'),
            ('S3→S4', '快速推進切（Smash Zoom Cut）', '旋轉結束時鏡頭快速推進（光學zoom或數位推進），在最近點切入特寫細節', 'At end of spin, rapid lens zoom-in push — at the closest point, hard cut into detail close-up'),
            ('S4→S5', '匹配切（Match Cut on Eye）', '最後一個細節特寫的光線或顏色，與眼神特寫的高光點匹配——靠色調連接兩個鏡頭', 'Match cut: color or light element in last detail shot matches catchlight or rim light in eye close-up — color bridge between shots'),
        ],
    },

    'drama_fashion': {
        'concept_cn': 'POV 反轉敘事——「被低估 → 震撼反轉 → 全場矚目」三段式情緒弧線，利用視角切換製造強烈反差感，觀眾代入旁觀者視角。',
        'concept_en': 'POV reversal narrative — "underestimated → shocking transformation → commanding presence" three-act emotional arc. Viewer adopts bystander POV for maximum vicarious impact.',
        'shots': [
            ('S1 — 建立低調（0–3s）', 'Establish Underdog', '手持輕微抖動的中景，主體低頭走入，燈光偏暗，服裝不起眼——刻意讓觀眾低估', 'Slightly unsteady handheld medium shot, subject enters with head down, dim lighting, understated outfit — deliberately underwhelming'),
            ('S2 — 轉折時刻（3–6s）', 'Pivot Moment', '主體慢慢抬頭/轉身，鏡頭開始從手持轉為穩定Steadicam跟拍，燈光開始升亮', 'Subject slowly raises head / turns, camera transitions from handheld to smooth Steadicam, lighting begins to brighten'),
            ('S3 — 大反轉（6–10s）', 'Power Reveal', '燈光全亮，鏡頭快速拉開至全身廣角，展示完整造型——停止移動，讓造型自己說話', 'Full lighting on, camera snaps to wide full-body to reveal complete look — camera stops completely, let the outfit do the talking'),
            ('S4 — 特寫強化（9–12s）', 'Authority Close-Up', '緩慢推進至半身近景，主體肩膀後展，直視鏡頭，眼神從溫柔轉為強勢，捕捉眼神變化的精確幀', 'Slow push to medium-close, shoulders roll back, subject locks eyes with camera — capture the exact frame where expression shifts from soft to powerful'),
            ('S5 — 離場收尾（12–15s）', 'Exit Shot', '主體轉身走遠，鏡頭不追（靜止），只看背影與裙擺/外套在光線中的輪廓——餘韻感', 'Subject turns and walks away, camera holds static — only see silhouette of back and garment hem/coat against light — lasting impression'),
        ],
        'transitions': [
            ('S1→S2', '燈光溶解（Light Dissolve）', '利用燈光從暗到亮的過程做0.5秒溶接，光線變化本身即是轉場', '0.5s dissolve driven by lighting change — the light transition IS the transition, no abrupt cut'),
            ('S2→S3', '動作硬切（Action Cut）', '主體完成轉身動作的最後一幀硬切至廣角全身，利用動作完成點做切入點', 'Hard cut at the exact completion frame of the turn — action endpoint is the cut point, creates satisfying "snap" to wide shot'),
            ('S3→S4', '靜止推進（Static Creep）', '不切，直接在廣角上做緩慢電動推進（不抖動），3秒內從全身推到半身近景', 'No cut — continuous slow motorized push-in from wide to medium-close over 3 seconds, zero shake'),
            ('S4→S5', '轉身遮幕（Turn Wipe）', '主體轉身動作帶動衣物/頭髮遮住鏡頭的瞬間，切入靜止背影遠景', 'Subject turn causes garment or hair to momentarily fill frame — cut to static far back-shot at that opaque frame'),
        ],
    },

    'beauty': {
        'concept_cn': '美妝前後對比——從素顏的真實感出發，逐步建立妝容，利用局部特寫放大細節質感，最終大揭幕製造驚艷感。',
        'concept_en': 'Beauty transformation — start with authentic bare-face, build the look step by step, use macro close-ups to showcase texture, end with a full-reveal wow moment.',
        'shots': [
            ('S1 — 素顏特寫（0–3s）', 'Bare Face Macro', '極近距離正面特寫（臉佔滿畫面），自然漫射光，無修飾，建立真實感與對比基準', 'Extreme close-up frontal (face fills frame), diffused natural light, no retouching — establishes authenticity and contrast baseline'),
            ('S2 — 上妝過程（3–9s）', 'Application Shots', '三個快切細節：a) 刷頭在皮膚上的micro close-up  b) 眼部上色特寫  c) 嘴唇上色的側面特寫——每個1.5秒', 'Three rapid detail cuts: a) brush-on-skin macro b) eye color application close-up c) lip color side-profile macro — 1.5s each'),
            ('S3 — 半完成鏡（optional）', 'Half-Done Reveal', '拉遠至臉部全景，左半完妝右半未妝（或自然過渡），強調對比感', 'Pull back to full face, left half complete look right half bare (or natural progression) — emphasize contrast'),
            ('S4 — 最終大揭幕（10–13s）', 'Final Reveal', '雙眼緩緩睜開，鏡頭從眼部微距緩慢拉遠至臉部全景，光線全開，高光打在顴骨和眼睛', 'Eyes slowly open from closed, camera gently pulls back from eye macro to full face, full lighting reveal, highlight on cheekbones and eyes'),
            ('S5 — 定格收尾（13–15s）', 'Beauty Hold', '靜止美妝定格：臉部3/4側角度，一道輪廓光從側面打亮，唇部或眼部微動（輕眨眼或微笑）', 'Static beauty hold: 3/4 face angle, single rim light from side, micro-movement — gentle blink or slow smile'),
        ],
        'transitions': [
            ('S1→S2', '遮幕推進（Beauty Wipe）', '第一個刷具入鏡的瞬間，刷具橫掃的方向做幕簾式切換至特寫', 'First brush entering frame — the sweep direction of the brush creates a curtain-wipe transition into close-up'),
            ('S2→S3', '焦點溶解（Focus Pull Dissolve）', '特寫失焦（鏡頭推出焦距），在模糊中溶接至拉遠的臉部全景', 'Defocus close-up (rack focus out) — transition through blur into the wider face shot (focus-pull dissolve)'),
            ('S3→S4', '眼睛睜開切（Eye-Open Cut）', '眼睛從閉合到睜開的瞬間做硬切，進入最終大特寫——眨眼本身就是轉場', 'Hard cut timed to the exact moment eyes open from closed — the eyelid opening IS the transition wipe'),
            ('S4→S5', '燈光凝固（Light Freeze）', '鏡頭拉遠動作逐漸停止，同時一道側面輪廓光緩緩打亮——靜止中的燈光移動代替轉場', 'Pull-back decelerates to zero as side rim light slowly intensifies — the arriving light replaces the need for a cut'),
        ],
    },

    'lifestyle': {
        'concept_cn': '生活美學Vlog——不是炫耀，是帶觀眾體驗一段有質感的日常時光。每個鏡頭都應該有環境感，讓人「聞到咖啡香」或「感受到早晨陽光」。',
        'concept_en': 'Aesthetic lifestyle Vlog — not showing off, but inviting the viewer to inhabit a moment. Every shot should be sensory: viewers should almost "smell the coffee" or "feel the morning sun."',
        'shots': [
            ('S1 — 環境建立（0–2s）', 'Establishing Environment', '純環境鏡（空景）：窗外樹影搖曳 / 桌上咖啡冒煙 / 晨光打在床鋪上——先讓觀眾感受氛圍，主體尚未入鏡', 'Environment-only shot (no subject yet): curtain moving / coffee steam rising / morning light on bed — let viewers feel the space before the subject enters'),
            ('S2 — 主體自然入鏡（2–5s）', 'Natural Entry', '手持跟隨鏡，主體自然走入或出現，鏡頭輕微滯後（不追得太緊），製造真實感', 'Handheld follow shot, subject naturally enters/appears, camera follows with slight lag — feels caught-off-guard, authentic'),
            ('S3 — 生活細節特寫（5–9s）', 'Life Detail Inserts', '2–3個快切細節：雙手捧杯 / 翻開書頁 / 望向窗外的側臉——記錄真實時刻的質感', '2–3 quick inserts: hands around mug / book page turning / profile face looking out window — texture of real moments'),
            ('S4 — 自然互動（8–12s）', 'Candid Moment', '鏡頭靜止等待，主體做某件事時偶然回頭發現鏡頭，產生「被偷拍到笑容」的真實感', 'Camera holds static and waits — subject doing something, turns and notices camera, creating the candid "caught smiling" authentic moment'),
            ('S5 — 詩意收尾（12–15s）', 'Poetic Close', '切回空景：咖啡杯旁邊的光影 / 窗外流動的樹影 / 床上被壓皺的位置——主體已不在畫面，留下存在的痕跡', 'Return to empty environment: light and shadow beside mug / drifting window shadow / impression in bedsheet — subject gone, only traces remain'),
        ],
        'transitions': [
            ('S1→S2', '聲音帶入（Sound-Led Cut）', '主體的腳步聲 / 咖啡杯聲先入，比畫面切換早0.5秒——聽覺引導視覺', 'Subject sound (footsteps / cup sound) enters 0.5s BEFORE the visual cut — audio leads video, sound cues the edit'),
            ('S2→S3', '視線引導切（Eyeline Match Cut）', '主體視線落在某個物件上的瞬間，切入該物件的特寫——遵循視線方向', 'Cut at the exact moment subject\'s eyes land on an object — cut to that object\'s close-up, following the eyeline direction'),
            ('S3→S4', '相似構圖匹配（Compositional Match Cut）', '找到兩個鏡頭中形狀相似的元素（圓形杯口 ↔ 圓形太陽 / 直線窗框 ↔ 書頁邊緣）做匹配切', 'Find compositionally similar shapes between shots (circular cup rim ↔ circular sun / window frame lines ↔ book edge) — match-cut on shape'),
            ('S4→S5', '搖鏡離場（Pan-Away Exit）', '在最真實笑容的瞬間，鏡頭緩緩搖離主體，轉向窗外或環境——主動結束凝視，給觀眾回味空間', 'At the peak candid smile moment, camera slowly pans away from subject toward window or environment — ending the gaze intentionally, leaving space for the viewer\'s emotion'),
        ],
    },
}


# ─── Output formatter ─────────────────────────────────────────────────────────

def build_prompt(video: dict, index: int) -> str:
    ct = classify(video)
    script = CONTENT_SCRIPTS[ct]
    title = video.get('title', '')[:70]
    platform = video.get('platform', 'youtube').upper()
    views = video.get('views', 0)
    likes = video.get('likes', 0)
    url = video.get('url', '')

    shots_cn = '\n'.join(
        f"  **{s[0]}**\n  {s[2]}"
        for s in script['shots']
    )
    shots_en = '\n'.join(
        f"  [{s[1]}]\n  {s[3]}"
        for s in script['shots']
    )
    trans_cn = '\n'.join(
        f"  **{t[0]} → {t[1]}**\n  {t[2]}"
        for t in script['transitions']
    )
    trans_en = '\n'.join(
        f"  [{t[0]}] {t[1]}\n  {t[3]}"
        for t in script['transitions']
    )

    return f"""
---

## #{index} — {platform} | 👁 {views:,} · 👍 {likes:,} | {ct.upper()}
**參考標題：** {title}
**參考連結：** {url}

### 📋 內容腳本（Content Script）

**中文概念：**
{script['concept_cn']}

**English Concept:**
{script['concept_en']}

---

### 🎬 分鏡畫面（Shot List）

**中文分鏡：**
{shots_cn}

**English Shot List:**
{shots_en}

---

### ✂️ 轉場方式（Transitions）

**中文轉場：**
{trans_cn}

**English Transitions:**
{trans_en}

---

### 🀄 Kling AI 完整 Prompt（貼上即用）
```
[套入你的人物樣板後開始]

內容：{script['concept_cn']}

分鏡：
{chr(10).join(f'• {s[0]}：{s[2]}' for s in script['shots'])}

轉場：
{chr(10).join(f'• {t[0]}→{t[1]}：{t[2]}' for t in script['transitions'])}

技術規格：9:16 豎屏，24fps 主軸搭配 120fps 慢動作片段，淺景深 f/1.8，總時長 12–15秒
```

### 🎞 Runway / Sora 完整 Prompt（貼上即用）
```
[Insert your character template here]

CONTENT: {script['concept_en']}

SHOT LIST:
{chr(10).join(f'• {s[1]}: {s[3]}' for s in script['shots'])}

TRANSITIONS:
{chr(10).join(f'• {t[0]}: {t[1]} — {t[3]}' for t in script['transitions'])}

SPECS: 9:16 vertical, 24fps cinematic with 120fps slo-mo inserts, shallow DOF f/1.8, total 12–15 seconds
```

"""


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--analysis', default=None)
    parser.add_argument('--output', default=OUTPUT_DIR)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--top', type=int, default=10)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.demo:
        import sys; sys.path.insert(0, os.path.dirname(__file__))
        from demo_data import DEMO_VIDEOS as videos
    else:
        if args.analysis:
            f = args.analysis
        else:
            files = sorted(glob.glob(os.path.join(PROCESSED_DIR, 'analysis_*.json')), reverse=True)
            if not files:
                print("找不到分析結果，請先執行 analyze.py 或加 --demo")
                return
            f = files[0]
        print(f"使用分析結果: {f}")
        data = json.load(open(f, encoding='utf-8'))
        videos = data.get('top_20_videos', [])

    videos = videos[:args.top]
    blocks = [build_prompt(v, i+1) for i, v in enumerate(videos)]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = os.path.join(args.output, f"ai_video_prompts_{timestamp}.md")

    header = f"""# AI 影片生成 Prompt — 內容 · 畫面 · 轉場 版

> 生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}
> 視頻數量：{len(videos)}
> 人物樣板：由你自行設定，Prompt 中以 [套入你的人物樣板] 標記插入位置

**使用方式：**
1. 確認你的人物樣板（外觀、服裝、基本描述）
2. 選一組 Prompt，將 `[套入你的人物樣板]` 替換為你的人物描述
3. 貼入 Kling / Runway / Sora 執行

---
"""

    with open(out, 'w', encoding='utf-8') as fp:
        fp.write(header)
        fp.write(''.join(blocks))

    print(f"✓ 已生成 {len(blocks)} 組【內容·畫面·轉場】Prompt")
    print(f"✓ 輸出至: {out}")
    return out


if __name__ == '__main__':
    main()
