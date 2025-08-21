import discord
from discord.ext import commands
import datetime
import re
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Data stores (in-memory)
balances = {}
last_claim = {}
bets = {}       # bet_id -> {name, yes_name, no_name, end_time, pool_yes, pool_no, wagers, resolved}
next_bet_id = 1

START_BALANCE = 100
DAILY_REWARD = 1

def get_balance(user_id):
    if user_id not in balances:
        balances[user_id] = START_BALANCE
        last_claim[user_id] = datetime.datetime.utcnow()
    else:
        # Daily reward check
        now = datetime.datetime.utcnow()
        delta_days = (now - last_claim[user_id]).days
        if delta_days >= 1:
            balances[user_id] += delta_days * DAILY_REWARD
            last_claim[user_id] = now
    return balances[user_id]

def parse_time(timestr):
    # Format like "10m 2h 1d"
    total = datetime.timedelta()
    matches = re.findall(r"(\d+)([smhd])", timestr)
    for val, unit in matches:
        val = int(val)
        if unit == "s":
            total += datetime.timedelta(seconds=val)
        elif unit == "m":
            total += datetime.timedelta(minutes=val)
        elif unit == "h":
            total += datetime.timedelta(hours=val)
        elif unit == "d":
            total += datetime.timedelta(days=val)
    return total

@bot.command()
async def bal(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"{ctx.author.mention} Balance: ${bal:.2f}")

@bot.command()
async def create(ctx, bet_name: str, *, time_str: str):
    global next_bet_id
    duration = parse_time(time_str)
    end_time = datetime.datetime.utcnow() + duration
    bet_id = next_bet_id
    next_bet_id += 1
    bets[bet_id] = {
        "name": bet_name,
        "end_time": end_time,
        "pool_yes": 0.0,
        "pool_no": 0.0,
        "wagers": [],  # (user_id, side, amount)
        "resolved": False
    }
    await ctx.send(f"Created bet {bet_id}: {bet_name} "
                   f"ends at {end_time} UTC")

@bot.command()
async def bid(ctx, bet_id: int, side: str, amount: float):
    if bet_id not in bets:
        await ctx.send("Invalid bet id")
        return
    bet = bets[bet_id]
    if bet["resolved"]:
        await ctx.send("This bet has already been resolved.")
        return

    side = side.lower()
    if side not in ["yes", "no"]:
        await ctx.send("Side must be 'yes' or 'no'")
        return
    bal = get_balance(ctx.author.id)
    if amount <= 0 or amount > bal:
        await ctx.send("Invalid bet amount")
        return

    balances[ctx.author.id] -= amount
    bet["wagers"].append((ctx.author.id, side, amount))
    if side == "yes":
        bet["pool_yes"] += amount
    else:
        bet["pool_no"] += amount
    await ctx.send(f"{ctx.author.mention} bet ${amount:.2f} on {side.upper()} for bet {bet_id}")

@bot.command()
async def lb(ctx):
    now = datetime.datetime.utcnow()
    active = [bid for bid, info in bets.items() if not info["resolved"] and info["end_time"] > now]
    if not active:
        await ctx.send("No active bets")
        return
    msg = "Active Bets:\n"
    for bid in active:
        info = bets[bid]
        msg += (f"ID {bid}: {info['name']} "
                f"Ends: {info['end_time']} UTC | "
                f"YES Pool: ${info['pool_yes']:.2f} | NO Pool: ${info['pool_no']:.2f}\n")
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def resolve(ctx, bet_id: int, winner: str):
    if bet_id not in bets:
        await ctx.send("Invalid bet id")
        return
    bet = bets[bet_id]
    if bet["resolved"]:
        await ctx.send("This bet is already resolved.")
        return

    winner = winner.lower()
    if winner not in ["yes", "no"]:
        await ctx.send("Winner must be 'yes' or 'no'")
        return

    pool_yes, pool_no = bet["pool_yes"], bet["pool_no"]
    total_winner_pool = pool_yes if winner == "yes" else pool_no
    total_loser_pool = pool_no if winner == "yes" else pool_yes

    # Payouts
    for user_id, side, amount in bet["wagers"]:
        if side == winner:
            if total_winner_pool > 0:
                payout = amount + (amount / total_winner_pool) * total_loser_pool
            else:
                payout = amount
            balances[user_id] = balances.get(user_id, START_BALANCE) + payout

    bet["resolved"] = True
    await ctx.send(f"Bet {bet_id} resolved! Winner: {winner.upper()}")

@bot.command()
async def ghelp(ctx):
    help_content = """!lb - lists bets
!bid <bet-id> <side (yes or no)> <amount> - bid some amount of money on an event occuring
!create <bet-name> <time> - create's a bet which will expire after time (xxh, xxm, xxs, xxd)
!bal - return's the current user's balance
!resolve (admin only) - resolve bet id with outcome (yes or no)"""
    await ctx.send(help_content)

@resolve.error
async def resolve_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to resolve bets.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---- Run ----
bot.run(os.getenv("BOT_TOKEN"))
