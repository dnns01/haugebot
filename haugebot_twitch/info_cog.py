import asyncio
import random
import sqlite3

from twitchio.ext import commands


@commands.core.cog()
class InfoCog:
    def __init__(self, bot):
        self.bot = bot

    async def info_loop(self):
        while True:
            sleep_duration = int(self.bot.get_setting("WusstestDuSchonLoop"))
            await asyncio.sleep(sleep_duration * 60)

            if await self.bot.stream():
                channel = self.bot.channel()
                color = self.bot.get_setting("WusstestDuSchonColor")
                prefix = self.bot.get_setting("WusstestDuSchonPrefix")
                message = self.get_random_message(prefix)
                await self.bot.send_me(channel, message, color)

    @staticmethod
    def get_random_message(prefix):
        conn = sqlite3.connect("db.sqlite3")

        c = conn.cursor()
        c.execute('SELECT text, use_prefix from haugebot_web_wusstestduschon where active is true')
        wusstestduschon = random.choice(c.fetchall())
        conn.close()

        if wusstestduschon[1] == 1:
            return prefix.strip() + " " + wusstestduschon[0].strip()
        else:
            return wusstestduschon[0]
