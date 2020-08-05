import os
import time

from dotenv import load_dotenv
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
pipi_timer = 0
pipi_votes = {}

# vote bot related
VOTE_DELAY_END = int(os.getenv("VOTE_DELAY_END"))
VOTE_DELAY_INTERIM = int(os.getenv("VOTE_DELAY_INTERIM"))
VOTE_MIN_VOTES = int(os.getenv("VOTE_MIN_VOTES"))
VOTE_COLOR = os.getenv("VOTE_COLOR")
VOTE_PLUS = os.getenv("VOTE_PLUS")
VOTE_MINUS = os.getenv("VOTE_MINUS")
VOTE_NEUTRAL = os.getenv("VOTE_NEUTRAL")
vote_first = 0
vote_last = 0
votes = {}

bot = commands.Bot(
    irc_token=IRC_TOKEN,
    prefix=PREFIX,
    nick=NICK,
    initial_channels=[CHANNEL]
)


def get_percentage(part, total):
    """ Calculate percentage """

    return round(part / total * 100, 1)


async def notify_pipi(ctx, use_timer=True, message=None):
    """ Write a message in chat, if there hasn't been a notification since PIPI_DELAY seconds. """

    global pipi_timer
    timestamp = time.time()

    if use_timer and timestamp < pipi_timer + PIPI_DELAY:
        return

    pipi_timer = timestamp
    vote_ctr = 0
    chatters = await bot.get_chatters(CHANNEL)

    if message is not None:
        await ctx.color(PIPI_COLOR_0)
        await ctx.send(message)
    else:
        for vote in pipi_votes.values():
            if vote == 1:
                vote_ctr += 1

        percentage = get_percentage(vote_ctr, chatters.count)

        vote_ctr = 20

        if vote_ctr == 0:
            await ctx.color(PIPI_COLOR_0)
            await ctx.send_me(f'Kein Druck (mehr) auf der Blase. Es kann fröhlich weiter gestreamt werden!')
        elif vote_ctr == 1:
            await ctx.color(PIPI_COLOR_1)
            await ctx.send_me(f'{vote_ctr} ({percentage}%) Mensch müsste mal')
        elif vote_ctr < PIPI_THRESHOLD_1:
            await ctx.color(PIPI_COLOR_1)
            await ctx.send_me(f'{vote_ctr} ({percentage}%) Menschen müssten mal')
        elif vote_ctr < PIPI_THRESHOLD_2:
            await ctx.color(PIPI_COLOR_2)
            await ctx.send_me(f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree')
        else:
            await ctx.color(PIPI_COLOR_3)
            await ctx.send_me(f'{vote_ctr} ({percentage}%) Menschen müssten mal haugeAgree haugeAgree')


async def notify_vote_result(ctx, final_result=False):
    votes_list = get_votes()

    output = f'{VOTE_PLUS} {votes_list[0][0]} ({votes_list[0][1]}%), ' \
             f'{VOTE_NEUTRAL} {votes_list[1][0]} ({votes_list[1][1]}%), ' \
             f'{VOTE_MINUS} {votes_list[2][0]} ({votes_list[2][1]}%) | '

    if final_result:
        output += f'Endergebnis'
    else:
        output += f'Zwischenergebnis'

    await ctx.channel.color(VOTE_COLOR)
    await ctx.channel.send_me(output)


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
        await ctx.color(PIPI_COLOR_0)
        await ctx.send_me("Jetzt geht noch mal jeder aufs Klo, und dann streamen wir weiter!")


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
async def event_message(ctx):
    global votes, vote_first, vote_last

    if ctx.content.startswith(PREFIX):
        await bot.handle_commands(ctx)
    else:

        # make sure the bot ignores itself and nightbot
        if ctx.author.name.lower() == [NICK.lower(), 'nightbot']:
            return

        # check if message is a vote
        msg = ctx.content
        if msg[:2] == '+-' or msg[:2] == '-+' or msg[:3] == '-/+' or msg[:3] == '+/-' or msg[:len(VOTE_NEUTRAL)] == VOTE_NEUTRAL:
            add_vote(ctx, 'neutral')
        elif msg[:1] == '+' or msg[:len(VOTE_PLUS)] == VOTE_PLUS:
            add_vote(ctx, 'plus')
        elif msg[:1] == '-' or msg[:len(VOTE_MINUS)] == VOTE_MINUS:
            add_vote(ctx, 'minus')

        # have X seconds passed since last vote? -> post end result
        if time.time() >= vote_last + VOTE_DELAY_END and vote_first != 0:
            # not enough votes?
            if len(votes) >= VOTE_MIN_VOTES:
                get_votes()
                await notify_vote_result(ctx, final_result=True)

            vote_first = 0
            vote_last = 0
            votes.clear()

        # have X seconds passed since first vote? -> post interim result
        if time.time() >= vote_first + VOTE_DELAY_INTERIM and vote_first != 0:
            if len(votes) >= VOTE_MIN_VOTES:
                vote_first = time.time()
                await notify_vote_result(ctx)


def add_vote(ctx, votetype):
    """adds votes to the votes-dict and sets timestamps"""
    global votes, vote_first, vote_last

    # is this the first vote?
    if vote_first == 0:
        vote_first = time.time()

    # should vote count as last (=newest) vote?
    if ctx.author.name not in votes or votes[ctx.author.name] != votetype:
        vote_last = time.time()

    # add vote to dict
    votes[ctx.author.name] = votetype


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


bot.run()
