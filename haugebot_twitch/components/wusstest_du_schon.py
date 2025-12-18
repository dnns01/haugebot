import asyncio
import datetime
import random
import sqlite3
from datetime import timedelta

from twitchio.ext import commands, routines

from haugebot_twitch import config


class WusstestDuSchon(commands.Component):
    def __init__(self, bot):
        self.bot = bot
        self.interval: int = 0
        self.loop.start()

    @routines.routine(delta=timedelta(minutes=1))
    async def loop(self):
        if await self.bot.stream():
            prefix = config.get_value("wusstest_du_schon_prefix")
            message = self.get_random_message(prefix)
            await self.bot.send(f"{datetime.datetime.now()}{message}")
            self.change_interval(config.get_int("wusstest_du_schon_loop"))

    @loop.before_routine
    async def before_loop(self):
        await self.bot.wait_until_ready()
        delay = 30 - datetime.datetime.now().second
        await asyncio.sleep(delay if delay > 0 else 60 + delay)

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

    def change_interval(self, new_interval: int) -> None:
        if new_interval != self.interval:
            self.loop.change_interval(delta=timedelta(minutes=new_interval), wait_first=True)
            self.interval = new_interval


# This is our entry point for the module.
async def setup(bot: commands.Bot) -> None:
    await bot.add_component(WusstestDuSchon(bot))
