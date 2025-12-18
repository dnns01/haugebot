import os
from datetime import datetime, timedelta

from twitchio import ChatMessage
from twitchio.ext import commands

from haugebot_twitch import vote_redis


class Vote(commands.Component):
    def __init__(self, bot):
        self.bot = bot
        self.DELAY_END = int(os.getenv("VOTE_DELAY_END"))
        self.DELAY_INTERIM = int(os.getenv("VOTE_DELAY_INTERIM"))
        self.MIN_VOTES = int(os.getenv("VOTE_MIN_VOTES"))
        self.PLUS = os.getenv("VOTE_PLUS")
        self.MINUS = os.getenv("VOTE_MINUS")
        self.NEUTRAL = os.getenv("VOTE_NEUTRAL")
        self.next_interim = None
        self.vote_end = None
        self.vote_blocked = None
        self.votes = {}
        self.redis = vote_redis.VoteRedis()

    # @routines.routine()
    async def manage_vote(self):
        if len(self.votes) > 0:
            if datetime.now() >= self.vote_end:
                await self.notify_vote_result(final_result=True)
                self.votes.clear()
                self.update_redis()
                self.vote_blocked = datetime.now() + timedelta(seconds=self.DELAY_INTERIM)
                return
            if datetime.now() >= self.next_interim:
                await self.notify_vote_result()
                self.next_interim = self.calc_next_interim()
        if self.vote_blocked and datetime.now() >= self.vote_blocked:
            self.vote_blocked = None

    @staticmethod
    def get_percentage(part, total):
        """ Calculate percentage """
        if total != 0:
            return round(part / total * 100, 1)

        return 0

    async def notify_vote_result(self, final_result: bool = False):
        if len(self.votes) < self.MIN_VOTES:
            return

        votes_list = self.get_votes()

        output = f'{self.PLUS} {votes_list[0][0]} ({votes_list[0][1]}%), ' \
                 f'{self.NEUTRAL} {votes_list[1][0]} ({votes_list[1][1]}%), ' \
                 f'{self.MINUS} {votes_list[2][0]} ({votes_list[2][1]}%) | '
        output += f'Endergebnis' if final_result else f'Zwischenergebnis'
        output += f' mit insgesamt {len(self.votes)} abgegebenen Stimmen'

        await self.bot.send(output)

    def get_votes(self):
        """analyzes the votes-dict and counts the votes"""
        plus = 0
        minus = 0
        neutral = 0

        # count values in dict
        for x in self.votes.values():
            if x == 'neutral':
                neutral += 1
            elif x == 'plus':
                plus += 1
            elif x == 'minus':
                minus += 1

        return [[plus, self.get_percentage(plus, len(self.votes))],
                [neutral, self.get_percentage(neutral, len(self.votes))],
                [minus, self.get_percentage(minus, len(self.votes))]]

    @commands.Component.listener()
    async def event_message(self, message: ChatMessage):
        # await self.bot.send(message.text)
        # await self.bot.send_announcement(message.text)
        #
        return
        # make sure the bot ignores itself and nightbot
        if not message.author or message.author.name.lower() in [self.bot.NICK.lower(), 'nightbot']:
            return

        # check if message is a vote
        msg = message.content
        if msg[:2] == '+-' or msg[:2] == '-+' or msg[:3] == '-/+' or msg[:3] == '+/-' or msg[:len(
                self.NEUTRAL)] == self.NEUTRAL:
            self.add_vote(message, 'neutral')
        elif msg[:1] == '+' or msg[:len(self.PLUS)] == self.PLUS:
            self.add_vote(message, 'plus')
        elif msg[:1] == '-' or msg[:len(self.MINUS)] == self.MINUS:
            self.add_vote(message, 'minus')

    def add_vote(self, ctx, votetype):
        """adds votes to the votes-dict and sets timestamps"""

        # Delay between two votes is not yet finished. So votes are not counted.
        if self.vote_blocked:
            return

        if len(self.votes) == 0:
            self.next_interim = self.calc_next_interim()

        # should vote extend voting?
        if ctx.author.name not in self.votes or self.votes[ctx.author.name] != votetype:
            self.vote_end = self.calc_vote_end()

        # add vote to dict
        self.votes[ctx.author.name] = votetype
        self.update_redis()

    def calc_next_interim(self):
        return datetime.now() + timedelta(seconds=self.DELAY_INTERIM)

    def calc_vote_end(self):
        return datetime.now() + timedelta(seconds=self.DELAY_END)

    def update_redis(self):
        """analyzes the votes-dict and counts the votes"""

        if self.redis.is_connected:
            votes = self.get_votes()
            p = self.redis.pipeline()  # start transaction
            p.set('plus', votes[0][0])
            p.set('neutral', votes[1][0])
            p.set('minus', votes[2][0])
            p.execute()  # transaction end


# This is our entry point for the module.
async def setup(bot: commands.Bot) -> None:
    await bot.add_component(Vote(bot))

# This is an optional teardown coroutine for miscellaneous clean-up if necessary.
# async def teardown(bot: commands.Bot) -> None:
#     ...
