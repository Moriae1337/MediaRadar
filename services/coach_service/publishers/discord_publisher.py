import logging
from typing import Dict
import requests

logger = logging.getLogger(__name__)


class DiscordPoster:
    """Publisher class for dispatching messages to Discord Webhooks.

    :param webhook_url: Discord Webhook endpoint URL.
    :type webhook_url: str
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.avatar_url = "https://i.pinimg.com/1200x/f4/56/ee/f456ee00743a38c74f0efbbfa2e2ce59.jpg"

    def post_coaching_report(self, report: Dict) -> bool:
        """Sends an organic direct chat message payload to Discord Webhook.

        :param report: Report payload containing message content and target username.
        :type report: Dict
        :return: True if Discord API accepts the payload (status 200/204), False otherwise.
        :rtype: bool
        """
        if not self.webhook_url:
            logger.error("Discord Webhook URL is missing!")
            return False

        username = report.get("username")
        message = report.get("message")

        if not message:
            logger.error("No chat message provided in report payload.")
            return False

        payload = {
            "username": "Aether",
            "avatar_url": self.avatar_url,
            "content": message,
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                logger.info(f"Successfully posted organic chat message for @{username} to Discord with Aether.")
                return True
            else:
                logger.error(f"Failed to post to Discord. Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception while posting to Discord webhook: {e}")
            return False
