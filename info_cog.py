import asyncio
import json
import os
import random

from twitchio.ext import commands


@commands.core.cog(name="InfoCog")
class InfoCog:
    def __init__(self, bot):
        self.bot = bot
        self.info_file = os.getenv("INFO_JSON")
        self.INFO_LOOP = int(os.getenv("INFO_LOOP"))
        self.INFO_COLOR = os.getenv("INFO_COLOR")
        self.info = []
        self.load_info()

    def load_info(self):
        """ Loads all info that should be sent to the chat regularly from INFO_JSON """

        info_file = open(self.info_file, mode='r')
        self.info = json.load(info_file)
        pass

    async def start_info_loop(self):
        asyncio.create_task(self.info_loop())

    async def info_loop(self):
        """ Send !pipimeter into the chat every x Minutes. Also check, whether the stream was offline for x Minutes.
         If this is true, reset the pipi counter, as you can assume, that the stream recently started."""

        while True:
            await asyncio.sleep(self.INFO_LOOP * 60)

            if await self.bot.stream():
                channel = self.bot.channel()
                message = f"Psssst... wusstest du eigentlich schon, {random.choice(self.info)}"
                await self.bot.send_me(channel, message, self.INFO_COLOR)
