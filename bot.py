import discord
from discord.ext import commands
import json
import os
import re
from dotenv import load_dotenv
from logparsing import parse_log

load_dotenv()
bot_token = os.getenv('bot_token')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print('Starting the bot.')
    channel = bot.get_channel(1071138999604891729)
    await channel.send('Initialized the bot.')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    await process_log(message)

    # Process other commands
    await bot.process_commands(message)

async def process_log(message):
    # Check if the message contains a valid link
    link_pattern = r'https:\/\/paste\.ee\/p\/\w+|https:\/\/mclo\.gs\/\w+'
    matches = re.findall(link_pattern, message.content)
    
    # Process each log link
    for match in matches:

        # Parse the log
        results = parse_log(match)

        # Check if there are results to send
        if results:
            # Join the results with newlines
            response = '\n'.join(results)

            # Send the message
            await message.channel.send(response)

            # Return to prevent sending a duplicate message
            return

bot.run(bot_token)
