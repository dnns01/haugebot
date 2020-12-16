import asyncio
import json
import logging
import os
import random
from datetime import datetime

from twitchio.ext import commands


@commands.core.cog(name="InfoCog")
class InfoCog:
    def __init__(self, bot):
        self.bot = bot
        self.info_file = os.getenv("INFO_JSON")
        self.INFO_LOOP = float(os.getenv("INFO_LOOP"))
        self.INFO_COLOR = os.getenv("INFO_COLOR")
        self.info = []
        self.load_info()

    def load_info(self):
        """ Loads all info that should be sent to the chat regularly from INFO_JSON """

        info_file = open(self.info_file, mode='r')
        self.info = json.load(info_file)

    async def info_loop(self):
        """ Send !pipimeter into the chat every x Minutes. Also check, whether the stream was offline for x Minutes.
         If this is true, reset the pipi counter, as you can assume, that the stream recently started."""

        logging.log(logging.INFO, f"Info loop started. {datetime.now()} {self}")

        while True:
            logging.log(logging.INFO, f"Inside Info loop. Sleep for {self.INFO_LOOP} minutes. {datetime.now()} {self}")
            await asyncio.sleep(self.INFO_LOOP * 60)
            logging.log(logging.INFO, f"Inside Info loop finished sleeping now. {datetime.now()} {self}")

            if await self.bot.stream():
                logging.log(logging.INFO,
                            f"Inside Info loop. Stream is online, so send a message now!!! {datetime.now()} {self}")
                channel = self.bot.channel()
                message = f"Psssst... wusstest du eigentlich schon, {random.choice(self.info)}"
                await self.bot.send_me(channel, message, self.INFO_COLOR)

            logging.log(logging.INFO,
                        f"Inside Info loop. Ooooookay, Loop ended, let's continue with the next round!!! {datetime.now()} {self}")
