import asyncio
import os

from twitchio.dataclasses import Message
from twitchio.ext import commands


@commands.core.cog(name="PipiCog")
class PipiCog:
    def __init__(self, bot):
        self.bot = bot
        self.DELAY = int(os.getenv("PIPI_DELAY"))
        self.THRESHOLD_1 = int(os.getenv("PIPI_THRESHOLD_1"))
        self.THRESHOLD_2 = int(os.getenv("PIPI_THRESHOLD_2"))
        self.PIPIMETER_LOOP = int(os.getenv("PIPIMETER_LOOP"))
        self.RESET_THRESHOLD = int(os.getenv("PIPI_RESET_THRESHOLD"))
        self.COLOR_0 = os.getenv("PIPI_COLOR_0")
        self.COLOR_1 = os.getenv("PIPI_COLOR_1")
        self.COLOR_2 = os.getenv("PIPI_COLOR_2")
        self.COLOR_3 = os.getenv("PIPI_COLOR_3")
        self.pipi_task = None
        self.pipi_votes = {}

    async def start_pipimeter_loop(self):
        asyncio.create_task(self.pipimeter_loop())

    async def notify_pipi(self, ctx, use_timer=True, message=None):
        """ Write a message in chat, if there hasn't been a notification since DELAY seconds. """

        if use_timer and self.pipi_task and not self.pipi_task.done():
            return

        if self.pipi_task:
            self.pipi_task.cancel()

        self.pipi_task = asyncio.create_task(self.pipi_block_notification())
        vote_ctr = 0
        chatters = await self.bot.chatters()

        if message is not None:
            await self.bot.send_me(ctx, message, self.COLOR_0)
        else:
            for vote in self.pipi_votes.values():
                if vote == 1:
                    vote_ctr += 1

            percentage = self.bot.get_percentage(vote_ctr, chatters.count)

            if vote_ctr == 0:
                await self.bot.send_me(ctx,
                                       f'Kein Druck (mehr) auf der Blase. Es kann fröhlich weiter gestreamt werden!',
                                       self.COLOR_0)
            elif vote_ctr == 1:
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Mensch müsste mal', self.COLOR_1)
            elif percentage < self.THRESHOLD_1:
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal', self.COLOR_1)
            elif percentage < self.THRESHOLD_2:
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree',
                                       self.COLOR_2)
            else:
                await self.bot.send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree haugeAgree',
                                       self.COLOR_3)

    async def pipi_block_notification(self):
        """ Just do nothing but sleep for DELAY seconds """

        await asyncio.sleep(self.DELAY)

    async def pipimeter_loop(self):
        """ Send !pipimeter into the chat every x Minutes. Also check, whether the stream was offline for x Minutes.
         If this is true, reset the pipi counter, as you can assume, that the stream recently started."""

        offline_since = 0

        while True:
            await asyncio.sleep(self.PIPIMETER_LOOP * 60)

            if await self.bot.stream():
                if offline_since >= self.RESET_THRESHOLD:
                    self.pipi_votes = {}
                offline_since = 0

                if len(self.pipi_votes) > 0:
                    channel = self.bot.channel()
                    message = Message(channel=channel)
                    await self.notify_pipi(message, use_timer=False)
            else:
                offline_since += self.PIPIMETER_LOOP

    @commands.command(name="pipi", aliases=["Pipi"])
    async def cmd_pipi(self, ctx):
        """ User mentioned there is a need to go to toilet. """

        self.pipi_votes[ctx.author.name] = 1
        await self.notify_pipi(ctx)

    @commands.command(name="warpipi", aliases=["Warpipi", "zuspät", "Zuspät"])
    async def cmd_warpipi(self, ctx):
        """ User already went to toilet. """

        if ctx.author.name in self.pipi_votes:
            self.pipi_votes[ctx.author.name] = 0
            await self.notify_pipi(ctx)

    @commands.command(name="pause", aliases=["Pause"])
    async def cmd_pause(self, ctx):
        """ We will do a break now! """

        if ctx.author.is_mod:
            self.pipi_votes = {}
            await self.bot.send_me(ctx, "Jetzt geht noch mal jeder aufs Klo, und dann streamen wir weiter!",
                                   self.COLOR_0)

    @commands.command(name="reset", aliases=["Reset"])
    async def cmd_reset(self, ctx):
        """ Reset pipi votes """

        if ctx.author.is_mod:
            self.pipi_votes = {}

    @commands.command(name="pipimeter", aliases=["Pipimeter"])
    async def cmd_pipimeter(self, ctx):
        if ctx.author.is_mod:
            await self.notify_pipi(ctx, use_timer=False)
