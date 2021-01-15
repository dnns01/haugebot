import asyncio
import logging
import sqlite3
from datetime import datetime

import config
from twitchio.dataclasses import Message
from twitchio.ext import commands


@commands.core.cog(name="PipiCog")
class PipiCog:
    def __init__(self, bot):
        self.bot = bot
        self.pipi_task = None

    async def notify_pipi(self, ctx, use_timer=True, message=None):
        """ Write a message in chat, if there hasn't been a notification since <PipiDelay> seconds. """

        if use_timer and self.pipi_task and not self.pipi_task.done():
            return

        if self.pipi_task:
            self.pipi_task.cancel()

        self.pipi_task = asyncio.create_task(self.pipi_block_notification())
        chatters = await self.bot.chatters()

        if message is not None:
            await self.bot.send_me(ctx, message, config.get_value("PipiColor0"))
        else:
            vote_ctr = self.get_pipimeter()

            percentage = self.bot.get_percentage(vote_ctr, chatters.count)

            if vote_ctr == 0:
                await self.bot.send_me(ctx,
                                       f'Kein Druck (mehr) auf der Blase. Es kann fröhlich weiter gestreamt werden!',
                                       config.get_value("PipiColor0"))
            elif vote_ctr == 1:
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Mensch müsste mal',
                                       config.get_value("PipiColor1"))
            elif percentage < config.get_int("PipiThreshold1"):
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal',
                                       config.get_value("PipiColor1"))
            elif percentage < config.get_int("PipiThreshold2"):
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree',
                                       config.get_value("PipiColor2"))
            else:
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree haugeAgree',
                                       config.get_value("PipiColor3"))

    async def pipi_block_notification(self):
        """ Just do nothing but sleep for <PipiDelay> seconds """

        await asyncio.sleep(config.get_int("PipiDelay"))

    async def pipimeter_loop(self):
        """ Send !pipimeter into the chat every x Minutes. Also check, whether the stream was offline for x Minutes.
         If this is true, reset the pipi counter, as you can assume, that the stream recently started."""

        logging.log(logging.INFO,
                    f"Pipi loop started To have an offset from Info loop, wait for one minute. {datetime.now()} {self}")
        offline_since = 0
        await asyncio.sleep(60)

        while True:
            pipimeter_loop = config.get_int("PipimeterLoop")
            logging.log(logging.INFO,
                        f"Inside Pipi loop. Sleep for {pipimeter_loop} minutes. {datetime.now()} {self}")
            await asyncio.sleep(pipimeter_loop * 60)
            logging.log(logging.INFO, f"Inside Pipi loop finished sleeping now. {datetime.now()} {self}")

            if await self.bot.stream():
                logging.log(logging.INFO,
                            f"Inside Pipi loop. Stream is online, so check for threshold!!! {datetime.now()} {self}")
                if offline_since >= config.get_int("PipimeterResetThreshold"):
                    self.truncate_pipimeter()
                offline_since = 0

                if self.get_pipimeter() > 0:
                    channel = self.bot.channel()
                    message = Message(channel=channel)
                    await self.notify_pipi(message, use_timer=False)
            else:
                offline_since += pipimeter_loop

            logging.log(logging.INFO,
                        f"Inside Pipi loop. Ooooookay, Loop ended, let's continue with the next round!!! {datetime.now()} {self}")

    @commands.command(name="pipi", aliases=["Pipi"])
    async def cmd_pipi(self, ctx):
        """ User mentioned there is a need to go to toilet. """

        self.add_pipimeter(ctx.author.name)
        await self.notify_pipi(ctx)

    @commands.command(name="warpipi", aliases=["Warpipi", "zuspät", "Zuspät"])
    async def cmd_warpipi(self, ctx):
        """ User already went to toilet. """

        if ctx.author.name:
            self.remove_pipimeter(ctx.author.name)
            await self.notify_pipi(ctx)

    @commands.command(name="pause", aliases=["Pause"])
    async def cmd_pause(self, ctx):
        """ We will do a break now! """

        if ctx.author.is_mod:
            self.truncate_pipimeter()
            await self.bot.send_me(ctx, "Jetzt geht noch mal jeder aufs Klo, und dann streamen wir weiter!",
                                   config.get_value("PipiColor0"))

    @commands.command(name="reset", aliases=["Reset"])
    async def cmd_reset(self, ctx):
        """ Reset pipi votes """

        if ctx.author.is_mod:
            self.truncate_pipimeter()

    @commands.command(name="pipimeter", aliases=["Pipimeter"])
    async def cmd_pipimeter(self, ctx):
        if ctx.author.is_mod:
            await self.notify_pipi(ctx, use_timer=False)

    def get_pipimeter(self):
        conn = sqlite3.connect("db.sqlite3")

        c = conn.cursor()
        c.execute('SELECT count(user) from haugebot_web_pipimeter')
        pipimeter = c.fetchone()[0]
        conn.close()

        return int(pipimeter)

    def truncate_pipimeter(self):
        conn = sqlite3.connect("db.sqlite3")

        c = conn.cursor()
        c.execute('DELETE from haugebot_web_pipimeter')
        conn.commit()
        conn.close()

    def add_pipimeter(self, user):
        conn = sqlite3.connect("db.sqlite3")

        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO haugebot_web_pipimeter(user) values (?)', (user,))
        conn.commit()
        conn.close()

    def remove_pipimeter(self, user):
        conn = sqlite3.connect("db.sqlite3")

        c = conn.cursor()
        c.execute('DELETE from haugebot_web_pipimeter where user = ?', (user,))
        conn.commit()
        conn.close()
