import asyncio
import logging
import os
import sqlite3
from abc import ABC

from dotenv import load_dotenv
from giveaway_cog import GiveawayCog
from info_cog import InfoCog
from pipi_cog import PipiCog
from twitchio.dataclasses import Context, Message, Channel
from twitchio.ext import commands
from vote_cog import VoteCog

logging.basicConfig(level=logging.INFO, filename='hausgeist.log')

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
        self.info_cog = InfoCog(self)
        self.pipi_cog = PipiCog(self)
        self.add_cog(GiveawayCog(self))
        self.add_cog(VoteCog(self))
        self.add_cog(self.info_cog)
        self.add_cog(self.pipi_cog)

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

        asyncio.create_task(self.info_cog.info_loop())
        asyncio.create_task(self.pipi_cog.pipimeter_loop())

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

    @staticmethod
    def get_setting(key):
        conn = sqlite3.connect("db.sqlite3")

        c = conn.cursor()
        c.execute('SELECT value from haugebot_web_setting where key = ?', (key,))
        value = c.fetchone()[0]
        conn.close()
        return value


bot = HaugeBot()


@bot.command(name="hauge-commands", aliases=["Hauge-commands", "haugebot-commands", "Haugebot-commands"])
async def cmd_haugebot_commands(ctx):
    await ctx.send(
        "Eine Liste mit den Commands des HaugeBot findest du unter: https://github.com/dnns01/TwitchHausGeist/blob/master/README.md")


bot.run()
