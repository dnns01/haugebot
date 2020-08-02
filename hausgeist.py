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
pipi_timer = 0
pipi_votes = {}

# vote bot related
VOTE_DELAY_END = int(os.getenv("VOTE_DELAY_END"))
VOTE_DELAY_INTERIM = int(os.getenv("VOTE_DELAY_INTERIM"))
VOTE_MIN_VOTES = int(os.getenv("VOTE_MIN_VOTES"))
plus = 0
minus = 0
neutral = 0
vote_first = 0
vote_last = 0
votes = {}
spammer = {}

bot = commands.Bot(
    irc_token=IRC_TOKEN,
    prefix=PREFIX,
    nick=NICK,
    initial_channels=[CHANNEL]
)


async def notify(ctx, use_timer=True):
    """ Write a message in chat, if there hasn't been a notification since PIPI_DELAY seconds. """

    global pipi_timer
    timestamp = time.time()

    if use_timer and timestamp < pipi_timer + PIPI_DELAY:
        return

    pipi_timer = timestamp
    vote_ctr = 0

    for vote in pipi_votes.values():
        if vote == 1:
            vote_ctr += 1
    if vote_ctr == 0:
        await ctx.send(f'/me Kein Druck (mehr) auf der Blase. Es kann fröhlich weiter gestreamt werden!')
    elif vote_ctr == 1:
        await ctx.send(f'/me {vote_ctr} Mensch müsste mal')
    else:
        await ctx.send(f'/me {vote_ctr} Menschen müssten mal')


@bot.event
async def event_ready():
    print('Logged in')


@bot.command(name="pipi")
async def cmd_pipi(ctx):
    """ User mentioned there is a need to go to toilet. """

    pipi_votes[ctx.author.name] = 1
    await notify(ctx)


@bot.command(name="warpipi")
async def cmd_warpipi(ctx):
    """ User already went to toilet. """

    if ctx.author.name in pipi_votes:
        pipi_votes[ctx.author.name] = 0
        await notify(ctx)


@bot.command(name="zuspät")
async def cmd_zuspaet(ctx):
    """ User was not to toilet. Now it is too late. """

    if ctx.author.name in pipi_votes and pipi_votes[ctx.author.name] == 1:
        pipi_votes[ctx.author.name] = 0
        await ctx.send(f'Für {ctx.author.name} ist es nun zu spät. {ctx.author.name} muss erst mal die Hose wechseln.')


@bot.command(name="pause")
async def cmd_pause(ctx):
    """ We will do a break now! """

    global pipi_votes

    if ctx.author.is_mod:
        pipi_votes = {}
        await ctx.send("/me Pipipause!!!")


@bot.command(name="reset")
async def cmd_pause(ctx):
    """ Reset pipi votes """

    global pipi_votes

    if ctx.author.is_mod:
        pipi_votes = {}


@bot.command(name="pipimeter")
async def cmd_pipimeter(ctx):
    if ctx.author.is_mod:
        await notify(ctx, use_timer=False)


@bot.event
async def event_message(ctx):
    global votes, vote_first, vote_last, spammer

    if ctx.content.startswith(PREFIX):
        await bot.handle_commands(ctx)
    else:

        # make sure the bot ignores itself and nightbot
        if ctx.author.name.lower() == [NICK.lower(), 'nightbot']:
            return

        # check if message is a vote
        msg = ctx.content
        if msg[:2] == '+-' or msg[:2] == '-+' or msg[:9] == 'haugeNeut':
            vote(ctx, 'neutral')
        elif msg[:1] == '+' or msg[:9] == 'haugePlus':
            vote(ctx, 'plus')
        elif msg[:1] == '-' or msg[:9] == 'haugeMinu':
            vote(ctx, 'minus')

        # have X seconds passed since last vote? -> post end result
        if time.time() >= vote_last + VOTE_DELAY_END and vote_first != 0:
            # not enough votes?
            if len(votes) < VOTE_MIN_VOTES:
                print(f'Not enough votes: {len(votes)}')
            else:
                get_votes()
                output = f'/me Plus: {plus} ({int(plus / len(votes) * 100)}%) + ' \
                         f'Neutral: {neutral} ({int(neutral / len(votes) * 100)}%) - ' \
                         f'Minus: {minus} ({100 - int(plus / len(votes) * 100) - int(neutral / len(votes) * 100)}%) ' \
                         f'Endergebnis nach {VOTE_DELAY_END} Sekunden ohne neuen Vote.'

                # spammer_top = max(spammer, key=spammer.get)
                # if spammer[spammer_top] >= 10:
                #     output = output + '@{} ({}) hör auf zu spammen!'.format(spammer_top,
                #                                                        spammer[spammer_top])
                await ctx.channel.send(output)
                print(f'Sending: {output}')

            vote_first = 0
            vote_last = 0
            votes.clear()
            spammer.clear()

        # have X seconds passed since first vote? -> post interim result
        if time.time() >= vote_first + VOTE_DELAY_INTERIM and vote_first != 0:
            # not enough votes?
            if len(votes) < VOTE_MIN_VOTES:
                print(f'Not enough votes: {len(votes)}')
                vote_first = 0
                vote_last = 0
                votes.clear()
                spammer.clear()
            else:
                vote_first = time.time()
                get_votes()
                output = f'/me Plus: {plus} ({int(plus / len(votes) * 100)}%) + ' \
                         f'Neutral: {neutral} ({int(neutral / len(votes) * 100)}%) - ' \
                         f'Minus: {minus} ({100 - int(plus / len(votes) * 100) - int(neutral / len(votes) * 100)}%) ' \
                         f'Zwischenergebnis nach {VOTE_DELAY_INTERIM} Sekunden durchgängige Votes.' \
 \
                await ctx.channel.send(output)
                print(f'Sending: {output}')


def vote(ctx, votetype):
    """adds votes to the votes-dict and sets timestamps"""
    global votes, vote_first, vote_last, spammer

    # is this the first vote?
    if vote_first == 0:
        vote_first = time.time()

    # new, changed or spam?
    if ctx.author.name in votes:
        if votes[ctx.author.name] == votetype:
            print(f'Vote spam: {ctx.author.name} - {votes[ctx.author.name]} -> {votetype}')
            if ctx.author.name in spammer:
                spammer[ctx.author.name] = spammer[ctx.author.name] + 1
            else:
                spammer[ctx.author.name] = 1
            # spammers dont' set vote_last, so they cannot extend the time a vote lasts.
        else:
            print(f'Vote changed: {ctx.author.name} - {votes[ctx.author.name]} -> {votetype}')
            # set time of last vote in case vote changed
            vote_last = time.time()
    else:
        print(f'Vote added: {ctx.author.name} - {votetype}')
        # set time of last vote in case it is a new vote
        vote_last = time.time()

    # add vote to dict
    votes[ctx.author.name] = votetype


def get_votes():
    """analyzes the votes-dict and counts the votes"""
    global plus, minus, neutral

    # reset global vars
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


bot.run()
