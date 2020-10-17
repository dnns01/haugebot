import os
from abc import ABC

from dotenv import load_dotenv
from twitchio.dataclasses import Context, Message, Channel
from twitchio.ext import commands

from giveaway_cog import GiveawayGog
from info_cog import InfoCog
from pipi_cog import PipiCog
from vote_cog import VoteCog

load_dotenv()
IRC_TOKEN = os.getenv("IRC_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
NICK = os.getenv("NICK")
CHANNEL = os.getenv("CHANNEL")
PREFIX = os.getenv("PREFIX")


class HaugeBot(commands.Bot, ABC):
    def __init__(self):
        self.IRC_TOKEN = os.getenv("IRC_TOKEN")
        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        self.NICK = os.getenv("NICK")
        self.CHANNEL = os.getenv("CHANNEL")
        self.PREFIX = os.getenv("PREFIX")
        super().__init__(irc_token=IRC_TOKEN, prefix=PREFIX, nick=NICK, initial_channels=[CHANNEL], client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET)
        self.pipi_cog = PipiCog(self)
        self.giveaway_cog = GiveawayGog(self)
        self.vote_cog = VoteCog(self)
        self.info_cog = InfoCog(self)
        self.add_cog(self.pipi_cog)
        self.add_cog(self.giveaway_cog)
        self.add_cog(self.vote_cog)
        self.add_cog(self.info_cog)

    @staticmethod
    async def send_me(ctx, content, color):
        """ Change Text color to color and send content as message """

        if type(ctx) is Context or type(ctx) is Channel:
            await ctx.color(color)
            await ctx.send_me(content)
        elif type(ctx) is Message:
            await ctx.channel.color(color)
            await ctx.channel.send_me(content)

    async def event_ready(self):
        print('Logged in')
        await self.pipi_cog.start_pipimeter_loop()
        await self.info_cog.start_info_loop()

    @staticmethod
    def get_percentage(part, total):
        """ Calculate percentage """
        if total != 0:
            return round(part / total * 100, 1)

        return 0

    def channel(self):
        return self.get_channel(self.CHANNEL)

    async def chatters(self):
        return await self.get_chatters(self.CHANNEL)

    async def stream(self):
        return await self.get_stream(self.CHANNEL)


bot = HaugeBot()


@bot.command(name="hauge-commands", aliases=["Hauge-commands", "haugebot-commands", "Haugebot-commands"])
async def cmd_haugebot_commands(ctx):
    await ctx.send(
        "Eine Liste mit den Commands des HaugeBot findest du unter: https://github.com/dnns01/TwitchHausGeist/blob/master/README.md")


bot.run()
