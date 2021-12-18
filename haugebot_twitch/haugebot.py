import os
from abc import ABC

from dotenv import load_dotenv
from twitchio import Channel, Message
from twitchio.ext.commands import Context, Bot

from vote_cog import VoteCog
from wusstest_du_schon import WusstestDuSchon
from wordcloud import Wordcloud


class HaugeBot(Bot, ABC):
    def __init__(self):
        self.IRC_TOKEN = os.getenv("IRC_TOKEN")
        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        self.NICK = os.getenv("NICK")
        self.CHANNEL = os.getenv("CHANNEL")
        self.PREFIX = os.getenv("PREFIX")
        super().__init__(token=self.IRC_TOKEN, prefix=self.PREFIX, nick=self.NICK, initial_channels=[self.CHANNEL],
                         client_id=self.CLIENT_ID,
                         client_secret=self.CLIENT_SECRET)
        self.add_cog(VoteCog(self))
        self.add_cog(WusstestDuSchon(self))
        self.add_cog(Wordcloud(self))

    @staticmethod
    async def send_me(ctx, content):
        """ Change Text color to color and send content as message """

        if type(ctx) is Context or type(ctx) is Channel:
            await ctx.send(f".me {content}")
        elif type(ctx) is Message:
            await ctx.channel.send(f".me {content}")

    async def event_ready(self):
        print('Logged in')

        if wusstest_du_schon := self.cogs.get("WusstestDuSchon"):
            wusstest_du_schon.loop.start()
        if vote_cog := self.cogs.get("VoteCog"):
            vote_cog.manage_vote.start()

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
        return await self._http.get_streams(user_logins=[self.CHANNEL])

    # @staticmethod
    # def get_setting(key):
    #     conn = sqlite3.connect("db.sqlite3")
    #
    #     c = conn.cursor()
    #     c.execute('SELECT value from haugebot_web_setting where key = ?', (key,))
    #     value = c.fetchone()[0]
    #     conn.close()
    #     return value


load_dotenv()
bot = HaugeBot()


@bot.command(name="hauge-commands", aliases=["Hauge-commands", "haugebot-commands", "Haugebot-commands"])
async def cmd_haugebot_commands(ctx):
    await ctx.send(
        "Eine Liste mit den Commands des HaugeBot findest du unter: https://github.com/dnns01/TwitchHausGeist/blob/master/README.md")


bot.run()
