import asyncio
import os
import time
from abc import ABC

import redis
from dotenv import load_dotenv
from twitchio.dataclasses import Context, Message, Channel
from twitchio.ext import commands

from giveaway_cog import GiveawayGog
from pipi_cog import PipiCog

load_dotenv()
IRC_TOKEN = os.getenv("IRC_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
NICK = os.getenv("NICK")
CHANNEL = os.getenv("CHANNEL")
PREFIX = os.getenv("PREFIX")

# vote bot related
VOTE_DELAY_END = int(os.getenv("VOTE_DELAY_END"))
VOTE_DELAY_INTERIM = int(os.getenv("VOTE_DELAY_INTERIM"))
VOTE_MIN_VOTES = int(os.getenv("VOTE_MIN_VOTES"))
VOTE_COLOR = os.getenv("VOTE_COLOR")
VOTE_PLUS = os.getenv("VOTE_PLUS")
VOTE_MINUS = os.getenv("VOTE_MINUS")
VOTE_NEUTRAL = os.getenv("VOTE_NEUTRAL")
vote_end_task = None
vote_interim_task = None
vote_task_new = None
votes = {}


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
        self.add_cog(self.pipi_cog)
        self.add_cog(self.giveaway_cog)

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

    @staticmethod
    def get_percentage(part, total):
        """ Calculate percentage """
        if total != 0:
            return round(part / total * 100, 1)

        return 0


bot = HaugeBot()

# redis-server related
R_HOST = os.getenv("REDIS_HOST")
R_PORT = os.getenv("REDIS_PORT")
R_DB = os.getenv("REDIS_DB")
R_PW = os.getenv("REDIS_PW")

useRedis = False

# try to connect
r = None
try:
    r = redis.Redis(host=R_HOST, port=R_PORT, db=R_DB, password=R_PW)
    print(r)
    r.ping()
    useRedis = True
    print('Redis: Connected!')
except Exception as ex:
    print('A connection to the Redis server could not be established. Redis querys are avoided.')

if useRedis and r:
    # update constants in Redis-DB
    r.set('voteMin', VOTE_MIN_VOTES)
    r.set('voteDelayEnd', VOTE_DELAY_END)
    r.set('voteDelayInter', VOTE_DELAY_INTERIM)

    # reset DB
    p = r.pipeline()  # start transaction
    p.set('plus', 0)
    p.set('neutral', 0)
    p.set('minus', 0)
    p.execute()  # transaction end


async def notify_vote_result(message, final_result=False):
    votes_list = get_votes()

    output = f'{VOTE_PLUS} {votes_list[0][0]} ({votes_list[0][1]}%), ' \
             f'{VOTE_NEUTRAL} {votes_list[1][0]} ({votes_list[1][1]}%), ' \
             f'{VOTE_MINUS} {votes_list[2][0]} ({votes_list[2][1]}%) | '
    output += f'Endergebnis' if final_result else f'Zwischenergebnis'
    output += f' mit insgesamt {len(votes)} abgegebenen Stimmen'

    await bot.send_me(message, output, VOTE_COLOR)


@bot.command(name="hauge-commands", aliases=["Hauge-commands", "haugebot-commands", "Haugebot-commands"])
async def cmd_haugebot_commands(ctx):
    await ctx.send(
        "Eine Liste mit den Commands des HaugeBot findest du unter: https://github.com/dnns01/TwitchHausGeist/blob/master/README.md")


@bot.event
async def event_message(message):
    global votes

    if message.content.startswith(PREFIX):
        await bot.handle_commands(message)
    else:

        # make sure the bot ignores itself and nightbot
        if message.author.name.lower() in [NICK.lower(), 'nightbot']:
            return

        # check if message is a vote
        msg = message.content
        if msg[:2] == '+-' or msg[:2] == '-+' or msg[:3] == '-/+' or msg[:3] == '+/-' or msg[:len(
                VOTE_NEUTRAL)] == VOTE_NEUTRAL:
            add_vote(message, 'neutral')
        elif msg[:1] == '+' or msg[:len(VOTE_PLUS)] == VOTE_PLUS:
            add_vote(message, 'plus')
        elif msg[:1] == '-' or msg[:len(VOTE_MINUS)] == VOTE_MINUS:
            add_vote(message, 'minus')

        if useRedis:
            # update redis-database
            update_redis()


def add_vote(ctx, votetype):
    """adds votes to the votes-dict and sets timestamps"""
    global votes, vote_end_task, vote_interim_task

    # Delay between two votes is not yet finished. So votes are not counted.
    if vote_task_new and not vote_task_new.done():
        return

    if len(votes) == 0:
        vote_end_task = asyncio.create_task(vote_end_voting(bot.get_channel(CHANNEL)))
        vote_interim_task = asyncio.create_task(vote_interim_voting(bot.get_channel(CHANNEL)))

    # should vote extend voting?
    if ctx.author.name not in votes or votes[ctx.author.name] != votetype:
        vote_end_task.set_name(int(time.time()))

    # add vote to dict
    votes[ctx.author.name] = votetype

    if useRedis:
        # update redis-database
        update_redis()


def update_redis():
    """analyzes the votes-dict and counts the votes"""
    plus = 0
    minus = 0
    neutral = 0

    # count values in dict
    for x in votes.values():
        if x == 'neutral':
            neutral += 1
        elif x == 'plus':
            plus += 1
        elif x == 'minus':
            minus += 1

    if useRedis:
        p = r.pipeline()  # start transaction
        p.set('plus', plus)
        p.set('neutral', neutral)
        p.set('minus', minus)
        p.execute()  # transaction end


def get_votes():
    """analyzes the votes-dict and counts the votes"""
    plus = 0
    minus = 0
    neutral = 0

    # count values in dict
    for x in votes.values():
        if x == 'neutral':
            neutral += 1
        elif x == 'plus':
            plus += 1
        elif x == 'minus':
            minus += 1

    return [[plus, bot.get_percentage(plus, len(votes))],
            [neutral, bot.get_percentage(neutral, len(votes))],
            [minus, bot.get_percentage(minus, len(votes))]]


async def vote_end_voting(channel):
    """ End a currently open voting """

    global vote_task_new

    # Wait for the initial VOTE_DELAY_END seconds
    await asyncio.sleep(VOTE_DELAY_END)

    # Check every second, if the delay has finished, because since VOTE_DELAY_END seconds there was no vote,
    # that extended the voting time
    while int(vote_end_task.get_name()) + VOTE_DELAY_END >= time.time():
        await asyncio.sleep(1)

    if len(votes) >= VOTE_MIN_VOTES:
        await notify_vote_result(channel, final_result=True)

    votes.clear()
    vote_task_new = asyncio.create_task(vote_block_votes())

    if useRedis:
        # update redis-database
        update_redis()


async def vote_interim_voting(channel):
    """ End a currently open voting """

    global vote_interim_task

    await asyncio.sleep(VOTE_DELAY_INTERIM)
    if not vote_end_task.done() and len(votes) >= VOTE_MIN_VOTES:
        await notify_vote_result(channel)
        vote_interim_task = asyncio.create_task(vote_interim_voting(bot.get_channel(CHANNEL)))

    if useRedis:
        # update redis-database
        update_redis()


async def vote_block_votes():
    """ Just do nothing but sleep for VOTE_DELAY_INTERIM seconds """

    await asyncio.sleep(VOTE_DELAY_INTERIM)


bot.run()
