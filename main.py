# This example requires the 'message_content' intent.

import logging
import os

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)

os.environ['PYTHONASYNCIODEBUG'] = '1'  # Enable asyncio debug mode
COMMAND_PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True

# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.command(name='hello', help='Replies with hello!')
async def hello(ctx):
    logging.info(f"Command invoked by {ctx.author.name} in {ctx.channel.name}")
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command(name='ping', help='Shows the bot\'s latency.')
async def ping(ctx):
    """
    Command: !ping
    Calculates and sends the bot's latency.
    """
    latency = bot.latency * 1000  # Latency in milliseconds
    await ctx.send(f'Pong! Latency: {latency:.2f}ms')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Invalid command. Try `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing a required argument for this command.")
    elif isinstance(error, commands.CommandInvokeError):
        print(f"Error in command {ctx.command}: {error.original}")
        await ctx.send("An error occurred while executing that command.")
    else:
        print(f"An unhandled error occurred: {error}")
        await ctx.send("An unexpected error occurred.")

@bot.event
async def on_ready():
    """This function is called when the bot successfully connects to Discord."""
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    # You can set the bot's presence (status) here
    await bot.change_presence(activity=discord.Game(name=f"Type {COMMAND_PREFIX}help"))

# If you define your own on_message, you MUST include bot.process_commands(message)
# for your commands to continue working.
@bot.event
async def on_message(message):
    """
    This function is called for EVERY message the bot can see.
    Be careful with what you do here, as it can run very often.
    """
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == bot.user:
        return

    # Example: Log messages to console
    logging.info(f"{message.guild.name}:{message.channel.name}:{message.author.global_name}:Msg: {message.content}")

    if "perl" in message.content.lower():
        await message.channel.send("I heard Python! I like Python.")

    # IMPORTANT: This line allows the bot to process commands.
    # If you have an on_message event, you NEED this line for commands to work.
    await bot.process_commands(message)

if __name__ == "__main__":
    token = os.getenv('APP_TOKEN')
    if not token:
        raise ValueError("Please set the APP_TOKEN environment variable.")
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print("ERROR: Failed to log in. Make sure your bot token is correct and you've enabled necessary intents in the Developer Portal.")
    except Exception as e:
        print(f"An error occurred while running the bot: {e}")
