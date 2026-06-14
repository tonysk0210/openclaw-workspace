#!/usr/bin/env python3
"""
YouTube Data API v3 - 抓取熱門美女短視頻
需要: pip install google-api-python-client
"""

import json
import os
import argparse
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fetch_videos(query, max_results, api_key, region_code='TW', order='relevance', months_back=6):
    youtube = build('youtube', 'v3', developerKey=api_key)

    # 計算 6 個月前的時間（RFC 3339 格式）
    since = datetime.now(timezone.utc) - timedelta(days=30 * months_back)
    published_after = since.strftime('%Y-%m-%dT%H:%M:%SZ')

    # 搜尋 Shorts 關鍵字
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        type='video',
        maxResults=max_results,
        order=order,
        regionCode=region_code,
        videoDuration='short',
        publishedAfter=published_after
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

    if not video_ids:
        print("未找到任何視頻")
        return []

    # 取得詳細統計數據
    stats_response = youtube.videos().list(
        part='statistics,snippet,contentDetails',
        id=','.join(video_ids)
    ).execute()

    videos = []
    for item in stats_response.get('items', []):
        stats = item.get('statistics', {})
        snippet = item.get('snippet', {})
        videos.append({
            'platform': 'youtube',
            'video_id': item['id'],
            'url': f"https://www.youtube.com/shorts/{item['id']}",
            'title': snippet.get('title', ''),
            'description': snippet.get('description', '')[:500],
            'channel': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', ''),
            'tags': snippet.get('tags', []),
            'category_id': snippet.get('categoryId', ''),
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
            'comments': int(stats.get('commentCount', 0)),
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'fetched_at': datetime.now().isoformat()
        })

    return videos


def is_excluded(video, exclude_keywords):
    """過濾不相關內容（遊戲、動畫、兒童、搞笑等）"""
    text = (video.get('title', '') + ' ' + video.get('description', '')).lower()
    return any(kw.lower() in text for kw in exclude_keywords)


def is_beauty_content(video, require_any):
    """確認是美女/時尚/生活相關內容"""
    text = (
        video.get('title', '') + ' ' +
        video.get('description', '') + ' ' +
        ' '.join(video.get('tags', []))
    ).lower()
    return any(kw.lower() in text for kw in require_any)


def main():
    parser = argparse.ArgumentParser(description='抓取 YouTube 熱門短視頻')
    parser.add_argument('--query', default=None, help='搜尋關鍵字（不指定則輪跑所有 queries）')
    parser.add_argument('--max-results', type=int, default=None)
    parser.add_argument('--months-back', type=int, default=6, help='只抓最近 N 個月的視頻（預設 6）')
    args = parser.parse_args()

    config = load_config()
    yt_cfg = config['youtube']
    api_key = yt_cfg['api_key']

    if api_key == 'YOUR_YOUTUBE_API_KEY':
        print("請先在 config.json 設定 YouTube API Key")
        return

    # 決定要跑哪些 query
    if args.query:
        queries = [args.query]
    else:
        queries = yt_cfg.get('queries', [yt_cfg['default_query']])

    max_results = args.max_results or yt_cfg.get('max_results', 30)
    exclude_kw = yt_cfg.get('exclude_keywords', [])
    require_any = yt_cfg.get('require_any_keywords', [])
    min_views = config['analysis']['min_views']
    min_likes = config['analysis']['min_likes']

    all_videos = {}  # 用 video_id 去重
    for query in queries:
        print(f"搜尋中: {query}")
        videos = fetch_videos(
            query=query,
            max_results=max_results,
            api_key=api_key,
            region_code=yt_cfg['region_code'],
            order=yt_cfg['order'],
            months_back=args.months_back
        )
        for v in videos:
            all_videos[v['video_id']] = v

    # 三層過濾：觀看門檻 + 黑名單排除 + 白名單確認
    filtered = [
        v for v in all_videos.values()
        if v['views'] >= min_views
        and v['likes'] >= min_likes
        and not is_excluded(v, exclude_kw)
        and (not require_any or is_beauty_content(v, require_any))
    ]

    # 按觀看數排序
    filtered.sort(key=lambda x: x['views'], reverse=True)

    print(f"\n共抓取 {len(all_videos)} 支（去重後），符合門檻且過濾後: {len(filtered)} 支")

    output_file = os.path.join(OUTPUT_DIR, f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"已儲存至: {output_file}")
    for v in filtered[:15]:
        print(f"  [{v['views']:>10,} 觀看 / {v['likes']:>7,} 讚] {v['title'][:65]}")


if __name__ == '__main__':
    main()
