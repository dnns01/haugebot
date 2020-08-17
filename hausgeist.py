import asyncio
import os
import time
import redis

from dotenv import load_dotenv
from twitchio.dataclasses import Context, Message, Channel
from twitchio.ext import commands

load_dotenv()
IRC_TOKEN = os.getenv("IRC_TOKEN")
NICK = os.getenv("NICK")
CHANNEL = os.getenv("CHANNEL")
PREFIX = os.getenv("PREFIX")

# pipibot related
PIPI_DELAY = int(os.getenv("PIPI_DELAY"))
PIPI_THRESHOLD_1 = int(os.getenv("PIPI_THRESHOLD_1"))
PIPI_THRESHOLD_2 = int(os.getenv("PIPI_THRESHOLD_2"))
PIPI_COLOR_0 = os.getenv("PIPI_COLOR_0")
PIPI_COLOR_1 = os.getenv("PIPI_COLOR_1")
PIPI_COLOR_2 = os.getenv("PIPI_COLOR_2")
PIPI_COLOR_3 = os.getenv("PIPI_COLOR_3")
pipi_task = None
pipi_votes = {}

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
votes = {}

bot = commands.Bot(
    irc_token=IRC_TOKEN,
    prefix=PREFIX,
    nick=NICK,
    initial_channels=[CHANNEL]
)

#redis-server related
R_HOST = os.getenv("REDIS_HOST")
R_PORT = os.getenv("REDIS_PORT")
R_DB = os.getenv("REDIS_DB")
R_PW = os.getenv("REDIS_PW")

useRedis = False

# try to connect
try:
    r = redis.Redis(host=R_HOST, port=R_PORT, db=R_DB, password=R_PW)
    print(r)
    r.ping()
    useRedis = True
    print('Redis: Connected!')
except Exception as ex:
    print('A connection to the Redis server could not be established. Redis querys are avoided.')


if useRedis:
    # update constants in Redis-DB
    r.set('pipiDelay', PIPI_DELAY)
    r.set('pipiT1', PIPI_THRESHOLD_1)
    r.set('pipiT2', PIPI_THRESHOLD_2)
    r.set('voteMin', VOTE_MIN_VOTES)
    r.set('voteDelayEnd', VOTE_DELAY_END)
    r.set('voteDelayInter', VOTE_DELAY_INTERIM)

    # reset DB
    p = r.pipeline() # start transaction
    p.set('plus', 0)
    p.set('neutral', 0)
    p.set('minus', 0)
    p.execute() # transaction end


def get_percentage(part, total):
    """ Calculate percentage """

    return round(part / total * 100, 1)


async def notify_pipi(ctx, use_timer=True, message=None):
    """ Write a message in chat, if there hasn't been a notification since PIPI_DELAY seconds. """

    global pipi_task

    if use_timer and pipi_task and not pipi_task.done():
        return

    if pipi_task:
        pipi_task.cancel()

    pipi_task = asyncio.create_task(pipi_block_notification())
    vote_ctr = 0
    chatters = await bot.get_chatters(CHANNEL)

    if message is not None:
        await send_me(ctx, message, PIPI_COLOR_0)
    else:
        for vote in pipi_votes.values():
            if vote == 1:
                vote_ctr += 1

        percentage = get_percentage(vote_ctr, chatters.count)

        if vote_ctr == 0:
            await send_me(ctx, f'Kein Druck (mehr) auf der Blase. Es kann fröhlich weiter gestreamt werden!',
                          PIPI_COLOR_0)
        elif vote_ctr == 1:
            await send_me(ctx, f'{vote_ctr} ({percentage}%) Mensch müsste mal', PIPI_COLOR_1)
        elif vote_ctr < PIPI_THRESHOLD_1:
            await send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal', PIPI_COLOR_1)
        elif vote_ctr < PIPI_THRESHOLD_2:
            await send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree', PIPI_COLOR_2)
        else:
            await send_me(ctx, f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree haugeAgree', PIPI_COLOR_3)


async def notify_vote_result(message, final_result=False):
    votes_list = get_votes()

    output = f'{VOTE_PLUS} {votes_list[0][0]} ({votes_list[0][1]}%), ' \
             f'{VOTE_NEUTRAL} {votes_list[1][0]} ({votes_list[1][1]}%), ' \
             f'{VOTE_MINUS} {votes_list[2][0]} ({votes_list[2][1]}%) | '
    output += f'Endergebnis' if final_result else f'Zwischenergebnis'

    await send_me(message, output, VOTE_COLOR)


async def send_me(ctx, content, color):
    """ Change Text color to color and send content as message """

    if type(ctx) is Context or type(ctx) is Channel:
        await ctx.color(color)
        await ctx.send_me(content)
    elif type(ctx) is Message:
        await ctx.channel.color(color)
        await ctx.channel.send_me(content)

@bot.event
async def event_ready():
    print('Logged in')


@bot.command(name="pipi")
async def cmd_pipi(ctx):
    """ User mentioned there is a need to go to toilet. """

    pipi_votes[ctx.author.name] = 1
    await notify_pipi(ctx)


@bot.command(name="warpipi")
async def cmd_warpipi(ctx):
    """ User already went to toilet. """

    if ctx.author.name in pipi_votes:
        pipi_votes[ctx.author.name] = 0
        await notify_pipi(ctx)


@bot.command(name="zuspät")
async def cmd_zuspaet(ctx):
    """ Alias to command "!warpipi" """

    await cmd_warpipi(ctx)


@bot.command(name="pause")
async def cmd_pause(ctx):
    """ We will do a break now! """

    global pipi_votes

    if ctx.author.is_mod:
        pipi_votes = {}
        await send_me(ctx, "Jetzt geht noch mal jeder aufs Klo, und dann streamen wir weiter!", PIPI_COLOR_0)


@bot.command(name="reset")
async def cmd_pause(ctx):
    """ Reset pipi votes """

    global pipi_votes

    if ctx.author.is_mod:
        pipi_votes = {}


@bot.command(name="pipimeter")
async def cmd_pipimeter(ctx):
    if ctx.author.is_mod:
        await notify_pipi(ctx, use_timer=False)


@bot.event
async def event_message(message):
    global votes

    if message.content.startswith(PREFIX):
        await bot.handle_commands(message)
    else:

        # make sure the bot ignores itself and nightbot
        if message.author.name.lower() == [NICK.lower(), 'nightbot']:
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
        p = r.pipeline() # start transaction
        p.set('plus', plus)
        p.set('neutral', neutral)
        p.set('minus', minus)
        p.execute() # transaction end

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

    return [[plus, get_percentage(plus, len(votes))],
            [neutral, get_percentage(neutral, len(votes))],
            [minus, get_percentage(minus, len(votes))]]


async def vote_end_voting(channel):
    """ End a currently open voting """

    # Wait for the initial VOTE_DELAY_END seconds
    await asyncio.sleep(VOTE_DELAY_END)

    # Check every second, if the delay has finished, because since VOTE_DELAY_END seconds there was no vote,
    # that extended the voting time
    while int(vote_end_task.get_name()) + VOTE_DELAY_END >= time.time():
        await asyncio.sleep(1)

    if len(votes) >= VOTE_MIN_VOTES:
        await notify_vote_result(channel, final_result=True)

    votes.clear()

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

async def pipi_block_notification():
    """ Just do nothing but sleep for PIPI_DELAY seconds """

    await asyncio.sleep(PIPI_DELAY)


bot.run()
