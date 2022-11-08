import discord, yaml
import commands

"""
Initialize client with default intents
"""
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

"""
I was thinking about using
an actual database here like maybe
sqlite or something but honestly a
key value store is probably fine.
"""
database = {}

"""
Bets are stored as a list of objects, the pot is just
some integer value for the dollars being bet
"""
bets = {}
pot = 0
admin = client.user

@client.event
async def on_ready():
    print(f"Logged in {client.user}")

@client.event
async def on_message(message: discord.Message):
    """
    When a message is sent by a user, the bot
    may receive this event as a message object
    """
    # don't resond to messages send by yourself
    if message.author == client.user:
        return

    """
    The '!' symbol will be used as the way to
    identify commands.
    """
    if message.content.startswith("!"):
        contents = message.content.split(' ')
        match contents[0]:
            case "!help":
                await commands.help(message)
            case "!bal":
                await commands.balance(message)
            case "!add":
                await commands.add(message)
            case "!bet":
                await commands.bet(message)
            case "!active_bets":
                await commands.active_bets(message)
            case _:
                print("invalid command")

if __name__ == "__main__":
    """
    Retrieve config file variables
    used to access the bot
    """
    with open("env.yaml", "r") as f:
        contents = f.read()
        f.close()
    keys = yaml.safe_load(contents)
    client.run(keys['BOT_TOKEN'])
