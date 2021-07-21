import json
import os
import uuid
from datetime import datetime

from twitchio.ext import commands, routines
from websockets import connect


def get_local_timezone():
    return datetime.now().astimezone().tzinfo


class Wordcloud(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.words = {}
        self.id = ""
        self.start_date = None
        self.ws_url = os.getenv("WORDCLOUD_WS_URL")
        self.secret = os.getenv("WORDCLOUD_SECRET")
        self.ws = None
        self.wordcloud_routine.start(self)

    @routines.routine(seconds=2)
    async def wordcloud_routine(self):
        try:
            if self.running:
                if not self.ws or self.ws.closed:
                    self.ws = await connect(self.ws_url)

                if self.ws:
                    js = {
                        "type": "word_update",
                        "secret": self.secret,
                        "uuid": str(self.id),
                        "start_date": self.start_date,
                        "words": self.sum_words()
                    }
                    print(js)
                    await self.ws.send(json.dumps(js))
            if not self.running:
                if self.ws and not self.ws.closed:
                    await self.ws.close()
        except Exception:
            pass

    @commands.command(name="wcloud")
    async def cmd_wcloud(self, ctx: commands.Context, phrase: str):
        if phrase in ["start", "stop"] and ctx.author.is_mod:
            if phrase == "start":
                self.running = True
                self.words = {}
                self.id = uuid.uuid4()
                self.start_date = datetime.now(tz=get_local_timezone()).isoformat(timespec="seconds")
            else:
                self.running = False
        else:
            self.words[ctx.author.name] = phrase

    def sum_words(self):
        words = {}
        for user, word in self.words.items():
            if count := words.get(word):
                words[word] = count + 1
            else:
                words[word] = 1

        return words
