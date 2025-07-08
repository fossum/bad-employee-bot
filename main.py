"""Discord Bad Employee Bot with Gemini AI responses."""

import logging
import os

import discord
from discord.ext import commands

from chat_history import ChatHelper, PSQLParams
from gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO)

# --- DevContainer Usage ---
db_connection_params = PSQLParams(
    dbname=os.getenv('BAD_EMPLOYEE_DB'),
    user=os.getenv('BAD_EMPLOYEE_USER'),
    password=os.getenv('BAD_EMPLOYEE_PASS'),
    host=os.getenv('BAD_EMPLOYEE_HOST'),
    port=os.getenv('BAD_EMPLOYEE_PORT')
)

with ChatHelper(db_connection_params) as chat_helper:
    chat_helper.verify_table()

os.environ['PYTHONASYNCIODEBUG'] = '1'  # Enable asyncio debug mode
COMMAND_PREFIX = "!"

ai_client = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))

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
    """Calculates and sends the bot's latency.

    Command: !ping
    """
    latency = bot.latency * 1000  # Latency in milliseconds
    await ctx.send(f'Pong! Latency: {latency:.2f}ms')

@bot.event
async def on_command_error(ctx, error):
    """Error handler for commands.

    Args:
        ctx (_type_): Discord client context.
        error (_type_): Error raised by the command.
    """
    # if isinstance(error, commands.CommandNotFound):
    #     await ctx.send("Invalid command. Try `!help` to see available commands.")
    if isinstance(error, commands.MissingRequiredArgument):
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
    """This function is called for EVERY message the bot can see.

    Be careful with what you do here, as it can run very often.
    """
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == bot.user:
        return

    # Log messages to console.
    logging.info(f"{message.guild.name}:{message.channel.name}:{message.author.global_name}:Msg: {message.clean_content}")
    with ChatHelper(db_connection_params) as chat_helper:
        chat_helper.save_chat_message(message)

        # Determine if the message is worthy of a response.
        if "perl" in message.content.lower():
            ai_response = await ai_client.generate_response(
                message, chat_helper.messages_from_user(message.author)
            )
            await message.channel.send(ai_response)

    # This line allows the bot to process commands.
    await bot.process_commands(message)


if __name__ == "__main__":
    token = os.getenv('DISCORD_APP_TOKEN')
    if not token:
        raise ValueError("Please set the DISCORD_APP_TOKEN environment variable.")
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print("ERROR: Failed to log in. Make sure your bot token is correct and you've enabled necessary intents in the Developer Portal.")
    except Exception as e:
        print(f"An error occurred while running the bot: {e}")
