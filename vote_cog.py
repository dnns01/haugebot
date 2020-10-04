import asyncio
import os
import time

from twitchio.ext import commands

import vote_redis


@commands.core.cog(name="VoteCog")
class VoteCog:
    def __init__(self, bot):
        self.bot = bot
        self.DELAY_END = int(os.getenv("VOTE_DELAY_END"))
        self.DELAY_INTERIM = int(os.getenv("VOTE_DELAY_INTERIM"))
        self.MIN_VOTES = int(os.getenv("VOTE_MIN_VOTES"))
        self.COLOR = os.getenv("VOTE_COLOR")
        self.PLUS = os.getenv("VOTE_PLUS")
        self.MINUS = os.getenv("VOTE_MINUS")
        self.NEUTRAL = os.getenv("VOTE_NEUTRAL")
        self.vote_end_task = None
        self.vote_interim_task = None
        self.vote_task_new = None
        self.votes = {}
        self.bot.add_listener(self.event_message)
        self.redis = vote_redis.VoteRedis()

    async def notify_vote_result(self, message, final_result=False):
        votes_list = self.get_votes()

        output = f'{self.PLUS} {votes_list[0][0]} ({votes_list[0][1]}%), ' \
                 f'{self.NEUTRAL} {votes_list[1][0]} ({votes_list[1][1]}%), ' \
                 f'{self.MINUS} {votes_list[2][0]} ({votes_list[2][1]}%) | '
        output += f'Endergebnis' if final_result else f'Zwischenergebnis'
        output += f' mit insgesamt {len(self.votes)} abgegebenen Stimmen'

        await self.bot.send_me(message, output, self.COLOR)

    async def vote_end_voting(self, channel):
        """ End a currently open voting """

        # Wait for the initial VOTE_DELAY_END seconds
        await asyncio.sleep(self.DELAY_END)

        # Check every second, if the delay has finished, because since VOTE_DELAY_END seconds there was no vote,
        # that extended the voting time
        while int(self.vote_end_task.get_name()) + self.DELAY_END >= time.time():
            await asyncio.sleep(1)

        if len(self.votes) >= self.MIN_VOTES:
            await self.notify_vote_result(channel, final_result=True)

        self.votes.clear()
        self.vote_task_new = asyncio.create_task(self.vote_block_votes())
        self.update_redis()

    async def vote_interim_voting(self, channel):
        """ End a currently open voting """

        await asyncio.sleep(self.DELAY_INTERIM)
        if not self.vote_end_task.done() and len(self.votes) >= self.MIN_VOTES:
            await self.notify_vote_result(channel)
            self.vote_interim_task = asyncio.create_task(
                self.vote_interim_voting(self.bot.get_channel(self.bot.CHANNEL)))

    async def vote_block_votes(self):
        """ Just do nothing but sleep for VOTE_DELAY_INTERIM seconds """

        await asyncio.sleep(self.DELAY_INTERIM)

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

        return [[plus, self.bot.get_percentage(plus, len(self.votes))],
                [neutral, self.bot.get_percentage(neutral, len(self.votes))],
                [minus, self.bot.get_percentage(minus, len(self.votes))]]

    async def event_message(self, message):
        # make sure the bot ignores itself and nightbot
        if message.author.name.lower() in [self.NICK.lower(), 'nightbot']:
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
        if self.vote_task_new and not self.vote_task_new.done():
            return

        if len(self.votes) == 0:
            self.vote_end_task = asyncio.create_task(self.vote_end_voting(self.bot.get_channel(self.bot.CHANNEL)))
            self.vote_interim_task = asyncio.create_task(
                self.vote_interim_voting(self.bot.get_channel(self.bot.CHANNEL)))

        # should vote extend voting?
        if ctx.author.name not in self.votes or self.votes[ctx.author.name] != votetype:
            self.vote_end_task.set_name(int(time.time()))

        # add vote to dict
        self.votes[ctx.author.name] = votetype
        self.update_redis()

    def update_redis(self):
        """analyzes the votes-dict and counts the votes"""

        if self.redis.is_connected:
            votes = self.get_votes()
            p = self.redis.pipeline()  # start transaction
            p.set('plus', votes[0][0])
            p.set('neutral', votes[1][0])
            p.set('minus', votes[2][0])
            p.execute()  # transaction end
