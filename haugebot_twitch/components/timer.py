import asyncio
import datetime
import os
import random
from datetime import datetime, date, timedelta, timezone

import aiohttp
import requests
from twitchio.ext import commands, routines


class Timer(commands.Component):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    @routines.routine(delta=timedelta(minutes=1))
    async def loop(self):
        now = datetime.now().replace(second=0, microsecond=0, tzinfo=timezone.utc)
        headers = {"secret": os.getenv("DJANGO_API_SECRET")}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{os.getenv('DJANGO_API_URI')}/api/get_timers") as r:
                timers = await r.json()
                for timer in timers.get("timers"):
                    if timer.get("active") and len(timer.get("texts")) > 0:
                        timer_texts = timer.get("texts")
                        next_time: date = datetime.fromisoformat(timer.get("next_time"))
                        if next_time <= now:
                            if await self.bot.stream():
                                if timer.get("announce"):
                                    await self.bot.announce(random.choice(timer_texts))
                                else:
                                    await self.bot.send(random.choice(timer_texts))
                            while next_time <= now:
                                next_time += timedelta(minutes=timer.get("interval"))

                            timer["next_time"] = next_time.isoformat().replace('+00:00', 'Z')
                            requests.post(f"{os.getenv('DJANGO_API_URI')}/api/update_timers/{timer.get('id')}",
                                          json=timer,
                                          headers=headers)

    @loop.before_routine
    async def before_loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60 - datetime.now().second)


# This is our entry point for the module.
async def setup(bot: commands.Bot) -> None:
    await bot.add_component(Timer(bot))
