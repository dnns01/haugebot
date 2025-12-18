import asyncio
import logging
import os

import twitchio
from dotenv import load_dotenv
from twitchio import eventsub
from twitchio.ext import commands

LOGGER: logging.Logger = logging.getLogger("Bot")


class HaugeBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            bot_id=os.getenv("BOT_ID"),
            owner_id=os.getenv("OWNER_ID"),
            prefix="!",
        )
        self.broadcaster_id = os.getenv("BROADCASTER_ID")

    async def setup_hook(self) -> None:
        subscription = eventsub.ChatMessageSubscription(broadcaster_user_id=self.broadcaster_id, user_id=self.bot_id)
        await self.subscribe_websocket(payload=subscription)

        await self.load_module("components.timer")
        # await self.load_module("components.wusstest_du_schon")

    async def event_ready(self) -> None:
        LOGGER.info("Logged in as: %s", self.user)

    async def stream(self):
        return await self.fetch_streams(user_ids=[self.broadcaster_id])

    async def send(self, message: str) -> None:
        user = self.create_partialuser(user_id=self.broadcaster_id)
        await user.send_message(message, sender=self.bot_id, source_only=True)

    async def announce(self, message: str) -> None:
        user = self.create_partialuser(user_id=self.broadcaster_id)
        await user.send_announcement(moderator=self.bot_id, message=message)


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with HaugeBot() as bot:
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    load_dotenv()
    main()
