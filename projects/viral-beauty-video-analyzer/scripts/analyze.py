#!/usr/bin/env python3
"""
分析收集到的視頻資料，提取內容模式
"""

import json
import os
import glob
from collections import Counter
from datetime import datetime

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')


def load_all_raw(latest_only=True):
    files = sorted(
        [f for f in glob.glob(os.path.join(RAW_DIR, '*.json')) if 'template' not in f],
        reverse=True
    )
    if not files:
        return []

    # 只取最新一批（同一天抓的所有檔）或全部
    if latest_only:
        latest_date = os.path.basename(files[0])[:15]  # youtube_YYYYMMDD
        files = [f for f in files if os.path.basename(f)[:15] >= latest_date]

    videos = []
    seen_ids = set()
    for f in files:
        with open(f, encoding='utf-8') as fp:
            data = json.load(fp)
            if isinstance(data, list):
                for v in data:
                    vid = v.get('video_id') or v.get('url', '')
                    if vid not in seen_ids:
                        seen_ids.add(vid)
                        videos.append(v)
    return videos


def analyze(videos):
    if not videos:
        print("沒有資料可以分析")
        return None

    # 按觀看數排序
    videos.sort(key=lambda x: x.get('views', 0), reverse=True)
    top_videos = videos[:20]

    # 統計 hashtags
    all_tags = []
    for v in videos:
        tags = v.get('tags', []) or v.get('hashtags', [])
        all_tags.extend([t.lower().strip('#') for t in tags])
    top_tags = Counter(all_tags).most_common(20)

    # 統計平台分布
    platform_dist = Counter(v.get('platform', 'unknown') for v in videos)

    # 統計場景類型（手動輸入資料才有）
    scene_types = Counter()
    outfit_types = Counter()
    action_types = Counter()
    for v in videos:
        if v.get('scene_description'):
            scene_types[v['scene_description'][:30]] += 1
        if v.get('outfit'):
            outfit_types[v['outfit'][:30]] += 1
        if v.get('actions'):
            action_types[v['actions'][:30]] += 1

    # 計算平均互動率
    total_views = sum(v.get('views', 0) for v in videos)
    total_likes = sum(v.get('likes', 0) for v in videos)
    avg_engagement = (total_likes / total_views * 100) if total_views > 0 else 0

    # 統計常見音樂
    music_counter = Counter(v.get('music', '') for v in videos if v.get('music'))

    result = {
        'analyzed_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'platform_distribution': dict(platform_dist),
        'avg_engagement_rate': round(avg_engagement, 2),
        'top_tags': top_tags,
        'top_music': music_counter.most_common(10),
        'scene_patterns': dict(scene_types.most_common(10)),
        'outfit_patterns': dict(outfit_types.most_common(10)),
        'action_patterns': dict(action_types.most_common(10)),
        'top_20_videos': [
            {
                'platform': v.get('platform'),
                'url': v.get('url'),
                'title': v.get('title', '')[:80],
                'views': v.get('views', 0),
                'likes': v.get('likes', 0),
                'hashtags': v.get('tags', []) or v.get('hashtags', []),
                'scene': v.get('scene_description', ''),
                'outfit': v.get('outfit', ''),
                'actions': v.get('actions', ''),
                'music': v.get('music', '')
            }
            for v in top_videos
        ]
    }

    return result


def print_summary(result):
    print(f"\n=== 分析結果摘要 ===")
    print(f"共分析 {result['total_videos']} 支視頻")
    print(f"平台分布: {result['platform_distribution']}")
    print(f"平均互動率: {result['avg_engagement_rate']}%")
    print(f"\nTop 10 Hashtags:")
    for tag, count in result['top_tags'][:10]:
        print(f"  #{tag}: {count} 次")
    print(f"\nTop 5 音樂:")
    for music, count in result['top_music'][:5]:
        print(f"  {music}: {count} 次")
    print(f"\nTop 5 視頻:")
    for v in result['top_20_videos'][:5]:
        print(f"  [{v['views']:>10,} 觀看] {v['title'][:50]} ({v['platform']})")


def main():
    videos = load_all_raw()
    print(f"載入 {len(videos)} 支視頻")

    result = analyze(videos)
    if not result:
        return

    print_summary(result)

    output_file = os.path.join(PROCESSED_DIR, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n分析結果已儲存: {output_file}")


if __name__ == '__main__':
    main()
