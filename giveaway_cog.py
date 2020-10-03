import os
import random

from twitchio.ext import commands


@commands.core.cog(name="GiveawayCog")
class GiveawayGog:
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_enabled = False
        self.giveaway_entries = {}
        self.COLOR = os.getenv("GIVEAWAY_COLOR")

    @commands.command(name="giveaway")
    async def cmd_giveaway(self, ctx):
        """ take part at the giveaway """

        if self.giveaway_enabled:
            self.giveaway_entries[ctx.author.name] = 1

    @commands.command(name="giveaway-open")
    async def cmd_giveaway_open(self, ctx):
        """ Reset and Open the giveaway """

        if ctx.author.is_mod:
            self.giveaway_enabled = True
            self.giveaway_entries = {}
            await self.bot.send_me(ctx,
                                   "Das Giveaway wurde gestartet. Schreibe !giveaway in den Chat um daran teilzunehmen.",
                                   self.COLOR)

    @commands.command(name="giveaway-reopen")
    async def cmd_giveaway_reopen(self, ctx):
        """ Reopen the giveaway after closing it (so reset) """

        if ctx.author.is_mod:
            self.giveaway_enabled = True
            await self.bot.send_me(ctx,
                                   "Das Giveaway wurde wieder geöffnet. Schreibe !giveaway in den Chat um daran teilzunehmen.",
                                   self.COLOR)

    @commands.command(name="giveaway-close")
    async def cmd_giveaway_close(self, ctx):
        """ Close the giveaway """

        if ctx.author.is_mod:
            self.giveaway_enabled = False
            await self.bot.send_me(ctx, "Das Giveaway wurde geschlossen. Es kann niemand mehr teilnehmen.", self.COLOR)

    @commands.command(name="giveaway-draw")
    async def cmd_giveaway_draw(self, ctx):
        """ Draw a giveaway winner """

        if ctx.author.is_mod:
            if len(self.giveaway_entries) > 0:
                winner = random.choice(list(self.giveaway_entries))
                entry_count = len(self.giveaway_entries)
                del self.giveaway_entries[winner]
                await self.bot.send_me(ctx,
                                       f"Es wurde aus {entry_count} Einträgen ausgelost. Und der Gewinner ist... @{winner}",
                                       self.COLOR)
            else:
                await self.bot.send_me(ctx, "Es muss Einträge geben, damit ein Gewinner gezogen werden kann.",
                                       self.COLOR)

    @commands.command(name="giveaway-reset")
    async def cmd_giveaway_reset(self, ctx):
        """ Reset giveaway entrys """

        if ctx.author.is_mod:
            self.giveaway_enabled = False
            self.giveaway_entries = {}
            await self.bot.send_me(ctx, "Das Giveaway wurde geschlossen und alle Einträge entfernt.", self.COLOR)
