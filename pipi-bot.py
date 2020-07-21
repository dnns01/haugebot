import os
import time

from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv()
IRC_TOKEN = os.getenv("IRC_TOKEN")
DELAY = int(os.getenv("DELAY"))
NICK = os.getenv("NICK")
CHANNEL = os.getenv("CHANNEL")
timer = 0
votes = {}

bot = commands.Bot(
    irc_token=IRC_TOKEN,
    prefix="!",
    nick=NICK,
    initial_channels=[CHANNEL]
)


async def notify(ctx, use_timer=True):
    """ Write a message in chat, if there hasn't been a notification since DELAY seconds. """

    global timer
    timestamp = time.time()

    if use_timer and timestamp < timer + DELAY:
        return

    timer = timestamp
    vote_ctr = 0

    for vote in votes.values():
        if vote == 1:
            vote_ctr += 1

    await ctx.send(f'/me {vote_ctr} Mensch(en) müssten mal')


@bot.event
async def event_ready():
    print('Logged in')


@bot.command(name="pipi")
async def cmd_pipi(ctx):
    """ User mentioned there is a need to go to toilet. """

    votes[ctx.author.name] = 1
    await notify(ctx)


@bot.command(name="warpipi")
async def cmd_warpipi(ctx):
    """ User already went to toilet. """

    if ctx.author.name in votes:
        votes[ctx.author.name] = 0
        await notify(ctx)


@bot.command(name="pause")
async def cmd_pause(ctx):
    """ We will do a break now! """

    global votes

    if ctx.author.is_mod:
        votes = {}
        await ctx.send("/me Pipipause!!!")


@bot.command(name="pipimeter")
async def cmd_pipimeter(ctx):
    if ctx.author.is_mod:
        await notify(ctx, use_timer=False)

bot.run()
