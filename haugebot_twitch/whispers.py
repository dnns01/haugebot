import sqlite3
from datetime import datetime

from twitchio.ext import commands


class Whispers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message):
        # make sure the bot ignores itself and nightbot
        if not message.author or message.author.name.lower() in [self.bot.NICK.lower(),
                                                                 'nightbot'] or message.channel is not None:
            return

        conn = sqlite3.connect("db.sqlite3")
        c = conn.cursor()
        c.execute(
            "INSERT INTO haugebot_web_whisper(author, content, received_at) VALUES (?, ?, ?)",
            (message.author.name, message.content, datetime.now()))
        conn.commit()
        conn.close()
