import argparse
import datetime
import logging
import sys
from pathlib import Path

# Ensure root directory is on PYTHONPATH
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from services.coach_service.analytics import MediaAnalyst
from services.coach_service.config import (
    DISCORD_WEBHOOK_URL,
    HISTORY_FILE,
    MAX_HISTORY_ENTRIES,
    PROFILE_URL,
    VIDEOS_TO_AUDIT,
)
from services.coach_service.intelligence import AICreatorCoach
from services.coach_service.publishers import DiscordPoster
from services.coach_service.storage import HistoryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("coach_service")


def run(dry_run: bool = False, profile_url: str = PROFILE_URL) -> None:
    """Executes the daily Media AI Creator Coach service cycle.

    :param dry_run: If True, skips sending webhook payloads to Discord.
    :type dry_run: bool, optional
    :param profile_url: Social profile URL or handle to analyze.
    :type profile_url: str, optional
    """
    logger.info("--- Starting Media Radar Media AI Creator Coach ---")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    time_of_day = "Morning" if now_utc.hour < 14 else "Evening"

    history = HistoryManager(HISTORY_FILE, MAX_HISTORY_ENTRIES)
    analyst = MediaAnalyst(profile_url)
    coach = AICreatorCoach()

    # Step 1: Fetch Profile Analytics
    analytics = analyst.analyze_profile(video_limit=VIDEOS_TO_AUDIT)
    if not analytics:
        logger.error(f"Could not retrieve analytics for profile: {profile_url}")
        return

    logger.info(
        f"Profile Audit complete: @{analytics['username']} | Avg Views: {analytics['avg_views']:,} | Avg Engagement: {analytics['avg_engagement_rate']}%"
    )

    # Step 2: Retrieve Natural Ongoing Chat Thread History
    history_context = history.get_long_term_memory_context(limit=50)

    # Step 3: Detect whether there is new activity / video upload
    has_new_activity = history.has_new_activity(analytics)
    mode = "audit" if has_new_activity else "checkin"

    logger.info(f"Generating natural {mode} media strategy chat ({time_of_day})...")
    report = coach.generate_report(analytics, history_context=history_context, time_of_day=time_of_day, mode=mode)

    poster = DiscordPoster(DISCORD_WEBHOOK_URL)

    top_video_id = analytics.get("top_video", {}).get("id") if analytics.get("top_video") else None

    if dry_run or not DISCORD_WEBHOOK_URL:
        logger.info(f"[DRY RUN / NO WEBHOOK] Daily AI Chat Message (Mode: {report.get('mode')}, Time: {time_of_day}):")
        logger.info(f"  Handle: @{report['username']}")
        logger.info(f"  Message: {report.get('message')}")

        snapshot = {
            "date": datetime.date.today().isoformat(),
            "timestamp": now_utc.isoformat(),
            "time_of_day": time_of_day,
            "username": report["username"],
            "avg_views": report["avg_views"],
            "avg_engagement": report["avg_engagement_rate"],
            "top_video_id": top_video_id,
            "mode": report.get("mode"),
            "message": report.get("message"),
        }
        history.add_report_snapshot(snapshot)
        history.save()
    else:
        success = poster.post_coaching_report(report)
        if success:
            snapshot = {
                "date": datetime.date.today().isoformat(),
                "timestamp": now_utc.isoformat(),
                "time_of_day": time_of_day,
                "username": report["username"],
                "avg_views": report["avg_views"],
                "avg_engagement": report["avg_engagement_rate"],
                "top_video_id": top_video_id,
                "mode": report.get("mode"),
                "message": report.get("message"),
            }
            history.add_report_snapshot(snapshot)
            history.save()
            logger.info("Successfully processed and recorded daily AI Coach report.")
        else:
            logger.warning("Failed to post AI Coach report to Discord.")

    logger.info("--- Execution completed successfully ---")


def main() -> None:
    """Main CLI entry point for coach_service."""
    parser = argparse.ArgumentParser(description="MediaRadar Media AI Creator Coach")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze profile and generate report without sending webhook requests to Discord",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=PROFILE_URL,
        help="Profile URL or username to audit",
    )
    args = parser.parse_args()

    run(dry_run=args.dry_run, profile_url=args.profile)


if __name__ == "__main__":
    main()
