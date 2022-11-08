import discord
import main
import util

async def help(message: discord.Message):
    s = ""
    with open("help.txt", "r") as f:
        s = f.read()
        f.close()
    await message.channel.send(s)

async def balance(message: discord.Message):
    amount = main.database.get(message.author, 0)
    await message.channel.send(f"{message.author} has ${amount} in cash")

async def add(message: discord.Message):
    try:
        amount = int(message.content.split(' ')[1])
        main.database[message.author] = main.database.get(message.author, 0) + amount
        await message.channel.send(f"added ${amount} to {message.author}'s cash")
    except Exception as e:
        await message.channel.send("ERROR: " + str(e))

async def bet(message: discord.Message):
    try:
        args = message.content.split(' ')
        amount, state = int(args[1]), args[2].lower()

        # get boolean of state
        if state == "false":
            state = False
        elif state == "true":
            state = True
        else:
            raise Exception("state is invalid")

        # getting the user's balance from our "database"
        user_balance = main.database.get(message.author, 0)
        if (user_balance < amount or amount < 0 or amount == 0):
            raise Exception("amount is invalid")

        # set user's new balance after the bet
        main.database[message.author] -= amount

        # main.bets.append(util.Bet(amount, state, message.author, main.pot))
        if message.author in main.bets:
            main.bets[message.author].update(amount)
        else:
            main.bets[message.author] = util.Bet(amount, state, message.author)
        await message.channel.send(f"{message.author} has bet ${amount}!")

    except Exception as e:
        await message.channel.send("ERROR: " + str(e))
        return

async def set_admin(message: discord.Message):
    """
    The bet admin, the person who manages the bets, this bet system
    is currently a work in progress
    """
    try:
        main.admin = message.content.split(' ')[1]
        await message.channel.send("admin has been updated!")
    except Exception as e:
        await message.channel.send("ERROR: " + str(e))

async def active_bets(message: discord.Message):
    try:
        for x in main.bets.values():
            await message.channel.send(f"user {x.user} bet ${x.amount}")
    except Exception as e:
        await message.channel.send("ERROR: " + str(e))

#TODO implement
async def start_bet():
    pass
async def conclude():
    pass

