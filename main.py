import asyncio

import discord
import json
import yt_dlp
from collections import deque
import ai_chat
from database import MusicDatabase
from discord.ext.commands import DefaultHelpCommand
import datetime
from discord.ext import commands

# Load token from token.json
with open("util/config.json", "r") as token_file:
    token_data = json.load(token_file)
    TOKEN = token_data["token"]
    OPENAI_TOKEN = token_data["openai_token"]
    SPOTIFY_CLIENT_ID = token_data["spotify_client_id"]
    SPOTIFY_CLIENT_SECRET = token_data["spotify_client_secret"]

YDL_OPTS = {
    'verbose': True,
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    # 'verbose': True,
    'outtmpl': 'audio/%(title)s.%(ext)s',
    'default_search': 'ytsearch',  # Set default search to YouTube
}

# @client.event
# async def on_ready():
#     print(f'We have logged in as {client.user}')
#     # Make sure the bot is ready to process commands
#     await client.change_presence(activity=discord.Game(name="!play"))


async def main():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix='$', intents=intents, help_command=DefaultHelpCommand())

    await bot.load_extension('cogs.ping')
    await bot.load_extension('cogs.music')
    # await bot.load_extension('cogs.player')

    await bot.start(TOKEN)

    # Add the MusicPlayer cog to the bot

if __name__ == "__main__":
    asyncio.run(main())
