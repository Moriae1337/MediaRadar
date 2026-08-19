import json
import logging
import re
from typing import Dict, Optional
import requests
import yt_dlp

logger = logging.getLogger(__name__)


class MediaAnalyst:
    """Analyst class for retrieving and computing social media profile analytics.

    :param profile_url: Full URL or handle of the target social media profile.
    :type profile_url: str
    """

    def __init__(self, profile_url: str):
        self.profile_url = profile_url

    def _fetch_profile_via_requests(self, username: str) -> Optional[Dict]:
        """Scrapes profile stats directly via HTML rehydration data.

        :param username: Clean handle/username of the creator.
        :type username: str
        :return: Dictionary containing scraped user statistics or None if failed.
        :rtype: Optional[Dict]
        """
        url = self.profile_url if "http" in self.profile_url else f"https://www.tiktok.com/@{username}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.6 Mobile/15E148 Safari/604.1"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', resp.text)
                if match:
                    data = json.loads(match.group(1))
                    user_info = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {})
                    stats = user_info.get("stats", {})
                    user = user_info.get("user", {})
                    return {
                        "username": user.get("uniqueId", username),
                        "nickname": user.get("nickname", username),
                        "sec_uid": user.get("secUid"),
                        "video_count": stats.get("videoCount", 0),
                        "follower_count": stats.get("followerCount", 0),
                        "heart_count": stats.get("heartCount", 0),
                    }
        except Exception as e:
            logger.debug(f"[MediaAnalyst] Requests scraping failed for @{username}: {e}")
        return None

    def analyze_profile(self, video_limit: int = 5) -> Optional[Dict]:
        """Fetches profile analytics and computes video performance metrics.

        :param video_limit: Maximum number of recent videos to analyze, defaults to 5.
        :type video_limit: int, optional
        :return: Structured profile analytics dictionary including recent video statistics.
        :rtype: Optional[Dict]
        """
        raw = self.profile_url.rstrip("/")
        username = raw.split("@")[-1].split("/")[0] if "@" in raw else raw.split("/")[-1]

        logger.info(f"[MediaAnalyst] Fetching profile analytics for @{username}...")

        profile_meta = self._fetch_profile_via_requests(username)
        sec_uid = profile_meta.get("sec_uid") if profile_meta else None

        videos = []
        urls_to_try = []
        if sec_uid:
            urls_to_try.append(f"tiktokuser:{sec_uid}")
        urls_to_try.append(self.profile_url if "http" in self.profile_url else f"https://www.tiktok.com/@{username}")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "playlistend": video_limit,
            "skip_download": True,
            "ignoreerrors": True,
            "logger": None,
        }

        for url in urls_to_try:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(url, download=False)
                    if result:
                        entries = result.get("entries", [])
                        if not entries and "id" in result:
                            entries = [result]

                        for entry in entries:
                            if not entry:
                                continue

                            video_id = entry.get("id")
                            title = entry.get("title", "Untitled Video")
                            views = entry.get("view_count", 0) or 0
                            likes = entry.get("like_count", 0) or 0
                            comments = entry.get("comment_count", 0) or 0
                            duration = entry.get("duration", 0) or 0
                            upload_date = entry.get("upload_date", "recent")
                            video_url = entry.get("webpage_url") or entry.get("url") or f"https://www.tiktok.com/@{username}/video/{video_id}"

                            engagement_rate = round(((likes + comments) / views * 100), 2) if views > 0 else 0.0

                            videos.append({
                                "id": video_id,
                                "title": title,
                                "url": video_url,
                                "views": views,
                                "likes": likes,
                                "comments": comments,
                                "duration": duration,
                                "upload_date": upload_date,
                                "engagement_rate": engagement_rate,
                            })
                        if videos:
                            break
            except Exception:
                pass

        video_count = len(videos) if videos else (profile_meta.get("video_count", 0) if profile_meta else 1)
        total_views = sum(v["views"] for v in videos)
        avg_views = int(total_views / len(videos)) if videos else 0
        avg_likes = int(sum(v["likes"] for v in videos) / len(videos)) if videos else (profile_meta.get("heart_count", 0) if profile_meta else 0)
        avg_engagement = round(sum(v["engagement_rate"] for v in videos) / len(videos), 2) if videos else 0.0

        top_video = max(videos, key=lambda v: v["views"]) if videos else None
        lowest_video = min(videos, key=lambda v: v["views"]) if videos else None

        return {
            "username": username,
            "profile_url": self.profile_url if "http" in self.profile_url else f"https://www.tiktok.com/@{username}",
            "video_count_audited": video_count,
            "avg_views": avg_views,
            "avg_likes": avg_likes,
            "avg_engagement_rate": avg_engagement,
            "top_video": top_video,
            "lowest_video": lowest_video,
            "recent_videos": videos,
        }
