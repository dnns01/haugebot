import random
import sqlite3

import config
from twitchio.ext import commands, routines


class WusstestDuSchon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @routines.routine(minutes=config.get_int("wusstest_du_schon_loop"))
    async def loop(self):
        if await self.bot.stream():
            channel = self.bot.channel()
            prefix = config.get_value("wusstest_du_schon_prefix")
            message = self.get_random_message(prefix)
            await self.bot.send_me(channel, message)

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

    def change_interval(self, minutes):
        pass