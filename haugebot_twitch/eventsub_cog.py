import os
from functools import partial

from twitchio.ext import eventsub, commands
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
client = commands.Bot.from_client_credentials(client_id, client_secret)

class EventSubCog(commands.Cog):
    def __init__(self, bot):
        global client

        self.bot = bot
        self.eventsub_client = eventsub.EventSubClient(client, "trololololo",
                                                       "https://bottest.copycat-games.de/haugebot/callback")
        self.bot.loop.create_task(self.eventsub_client.listen(port=23456))

    async def subscribe(self):
        for subscription in await self.eventsub_client.get_subscriptions():
            await self.eventsub_client.delete_subscription(subscription.id)
        await self.eventsub_client.subscribe_channel_stream_start(87637599)
        await self.eventsub_client.subscribe_channel_stream_end(87637599)
        lol = await self.eventsub_client.get_subscriptions()
        print(lol)

    @client.event()
    async def event_eventsub_notification_stream_start(payload: eventsub.NotificationEvent):
        print(payload)

    @client.event()
    async def event_eventsub_notification_stream_end(payload: eventsub.NotificationEvent):
        print(payload)
