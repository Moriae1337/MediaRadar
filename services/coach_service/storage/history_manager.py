import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages history tracking, snapshot storage, and context compaction for coaching sessions.

    :param history_file: Path to the JSON history storage file.
    :type history_file: Path
    :param max_entries: Maximum number of entries to retain, defaults to 1000.
    :type max_entries: int, optional
    """

    def __init__(self, history_file: Path, max_entries: int = 1000):
        self.history_file = history_file
        self.max_entries = max_entries
        self.history_data = []
        self.load()

    def load(self) -> None:
        """Loads historical coach reports from JSON file into memory."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history_data = data.get("reports", [])
                    logger.info(f"Loaded {len(self.history_data)} daily coach reports from history.")
            except Exception as e:
                logger.error(f"Failed to read history file: {e}. Starting fresh.")
                self.history_data = []
        else:
            self.history_data = []

    def get_last_snapshot(self) -> Optional[Dict]:
        """Returns the most recent analytics snapshot from history.

        :return: Most recent snapshot dictionary or None if history is empty.
        :rtype: Optional[Dict]
        """
        if self.history_data:
            return self.history_data[-1]
        return None

    def get_long_term_memory_context(self, limit: int = 50) -> str:
        """Formats past chat history as an ongoing natural Discord thread with automatic smart compaction.

        :param limit: Maximum number of recent sessions to include, defaults to 50.
        :type limit: int, optional
        :return: Formatted long-term memory context string.
        :rtype: str
        """
        if not self.history_data:
            return "This is the start of our ongoing Discord chat thread. No previous messages."

        sessions_slice = self.history_data[-limit:]

        if len(sessions_slice) > 15:
            older = sessions_slice[:-10]
            recent = sessions_slice[-10:]

            first_date = older[0].get("date", "")
            last_older_date = older[-1].get("date", "")
            views_start = older[0].get("avg_views", 0)
            views_end = older[-1].get("avg_views", 0)

            compacted_summary = (
                f"SUMMARY OF PAST CHAT & ADVICE ({len(older)} messages from {first_date} to {last_older_date}):\n"
                f"- Channel views trajectory: moved from {views_start:,} to {views_end:,} avg views.\n"
                f"- Past advice topics already discussed: video hook timing (0.5s), comment pinning strategy, posting frequency, velocity presets, and title optimization.\n\n"
                f"RECENT CONVERSATION THREAD:\n"
            )

            for snap in recent:
                date = snap.get("date", "Date")
                tod = snap.get("time_of_day", "Check-in")
                msg = snap.get("message") or snap.get("chat_message") or ""
                if msg:
                    compacted_summary += f"[{date} - {tod} Check-in]\n{msg}\n\n"

            return compacted_summary.strip()

        conversation_log = "PREVIOUS DISCORD CHAT MESSAGES IN THIS THREAD:\n\n"
        for snap in sessions_slice:
            date = snap.get("date", "Date")
            tod = snap.get("time_of_day", "Check-in")
            msg = snap.get("message") or snap.get("chat_message") or ""
            if msg:
                conversation_log += f"[{date} - {tod} Check-in]\n{msg}\n\n"

        return conversation_log.strip()

    def has_new_activity(self, current_analytics: Dict) -> bool:
        """Determines if there is a new video uploaded or significant metric change.

        :param current_analytics: Dictionary of fresh profile metrics.
        :type current_analytics: Dict
        :return: True if new activity or metric shift is detected, False otherwise.
        :rtype: bool
        """
        last_snap = self.get_last_snapshot()
        if not last_snap:
            return True

        last_top_id = last_snap.get("top_video_id")
        current_top_id = current_analytics.get("top_video", {}).get("id") if current_analytics.get("top_video") else None

        last_avg_views = last_snap.get("avg_views", 0)
        current_avg_views = current_analytics.get("avg_views", 0)

        if current_top_id and current_top_id != last_top_id:
            logger.info("[HistoryManager] New top video detected!")
            return True

        if last_avg_views > 0:
            change_ratio = abs(current_avg_views - last_avg_views) / last_avg_views
            if change_ratio >= 0.02:
                logger.info(f"[HistoryManager] View metric shift detected ({change_ratio*100:.1f}% change).")
                return True

        logger.info("[HistoryManager] No new activity detected since last run.")
        return False

    def add_report_snapshot(self, report: dict) -> None:
        """Appends a new report snapshot to the history sequence.

        :param report: Report snapshot dictionary to record.
        :type report: dict
        """
        self.history_data.append(report)

    def save(self) -> None:
        """Saves current memory history state to the JSON storage file."""
        if len(self.history_data) > self.max_entries:
            self.history_data = self.history_data[-self.max_entries:]

        data = {"reports": self.history_data}
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.history_data)} report snapshot(s) to history.")
        except Exception as e:
            logger.error(f"Failed to save history file: {e}")
