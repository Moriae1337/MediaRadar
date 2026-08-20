import json
import logging
import time
from pathlib import Path
from typing import Dict
import requests
from services.coach_service.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

PROMPTS_FILE = Path(__file__).resolve().parent.parent / "config" / "prompts.json"


class AICreatorCoach:
    """AI Creator Coach service for generating video editing and media strategy advice.

    :param api_key: Google Gemini API Key, defaults to GEMINI_API_KEY.
    :type api_key: str
    """

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        """Loads prompt templates from JSON configuration file.

        :return: Dictionary containing prompt templates.
        :rtype: Dict[str, str]
        """
        if PROMPTS_FILE.exists():
            try:
                with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[AICreatorCoach] Error loading prompts JSON: {e}")
                raise e
        return {}

    def generate_report(
        self,
        analytics: Dict,
        history_context: str = "",
        time_of_day: str = "Daily",
        mode: str = "checkin",
    ) -> Dict:
        """Generates a video editing and media strategy check-in message.

        :param analytics: Profile metrics dictionary retrieved from analyst.
        :type analytics: Dict
        :param history_context: Past conversation history thread, defaults to "".
        :type history_context: str, optional
        :param time_of_day: Check-in period (Morning or Evening), defaults to "Daily".
        :type time_of_day: str, optional
        :param mode: Execution mode (audit or checkin), defaults to "checkin".
        :type mode: str, optional
        :return: Report dictionary containing username, metrics, mode, and generated message.
        :rtype: Dict
        """
        username = analytics["username"]
        logger.info(f"[AICreatorCoach] Generating video editing & media strategy check-in ({mode}, {time_of_day}) for @{username}...")

        msg = self._query_gemini(analytics, history_context, time_of_day)
        return {
            "username": username,
            "avg_views": analytics.get("avg_views", 0),
            "avg_engagement_rate": analytics.get("avg_engagement_rate", 0.0),
            "time_of_day": time_of_day,
            "mode": mode,
            "message": msg,
        }

    def _query_gemini(self, analytics: Dict, history_context: str, time_of_day: str = "Daily") -> str:
        """Queries Google Gemini LLM API to produce continuous chat messages.

        :param analytics: Profile metrics dictionary.
        :type analytics: Dict
        :param history_context: Past conversation context string.
        :type history_context: str
        :param time_of_day: Current check-in time of day, defaults to "Daily".
        :type time_of_day: str, optional
        :return: Natural continuous chat response text.
        :rtype: str
        """
        username = analytics.get("username", "creator")

        if not self.api_key:
            logger.error("[AICreatorCoach] GEMINI_API_KEY is missing!")
            raise RuntimeError("GEMINI_API_KEY is missing!")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.api_key}"

        system_instruction = self.prompts.get(
            "system_instruction",
            "You are a senior video editor and media strategist sending a self-contained twice-daily check-in message."
        ).format(
            username=username,
            time_of_day=time_of_day,
        )

        prompt_template = self.prompts.get(
            "prompt_template",
            "Stats for @{username}: Avg Views: {avg_views}\nRecent Chat:\n{previous_coaching_history}"
        )

        recent_titles = [v["title"] for v in analytics.get("recent_videos", [])]
        top_vid = analytics.get("top_video") or {}

        prompt = prompt_template.format(
            username=username,
            avg_views=f"{analytics.get('avg_views', 0):,}",
            avg_engagement_rate=analytics.get("avg_engagement_rate", 0.0),
            video_count_audited=analytics.get("video_count_audited", 0),
            top_video_title=top_vid.get("title", "N/A"),
            top_video_views=f"{top_vid.get('views', 0):,}",
            recent_titles=recent_titles,
            time_of_day=time_of_day,
            previous_coaching_history=history_context or "No previous check-in messages.",
        )

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.65,
            },
        }

        # Send request with a 35-second timeout and 1 automatic retry on ReadTimeout
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                resp = requests.post(url, json=payload, timeout=35)
                if resp.status_code == 200:
                    result_json = resp.json()
                    text = result_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return text
                else:
                    err_msg = f"[AICreatorCoach] Gemini API returned status {resp.status_code}: {resp.text}"
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)
            except requests.exceptions.Timeout as e:
                logger.warning(f"[AICreatorCoach] Gemini API call timed out on attempt {attempt}/{max_attempts}: {e}")
                if attempt == max_attempts:
                    raise e
                time.sleep(2)
            except Exception as e:
                logger.error(f"[AICreatorCoach] Error calling Gemini API: {e}")
                raise e
