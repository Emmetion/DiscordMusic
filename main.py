import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import json
import yt_dlp
import nacl
import asyncio
from collections import deque
import ai_chat
from database import MusicDatabase
import datetime

# Load token from token.json
with open("config.json", "r") as token_file:
    token_data = json.load(token_file)
    TOKEN = token_data["token"]
    OPENAI_TOKEN = token_data["openai_token"]

ydl_opts = {
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

class MyClient(discord.Client):
    __slots__ = ["__queue", "__player", "__openai", "__db"]

    async def on_ready(self):
        self.__db = MusicDatabase()

        print(f'Logged on as {self.user}!')

        self.__queue = deque()
        self.__player = None  # the voice_client.
        await self.get_channel(1205275052266889316).connect()
        msg = self.get_channel(1205275051025506318)
        message = await msg.send("Joining voice")

        self.__openai = ai_chat.OpenAIChat(openai_token=OPENAI_TOKEN)

        await self.play_youtube(message, "https://www.youtube.com/watch?v=2t5gC28Z_PI")
        await self.play_youtube(message, "https://www.youtube.com/watch?v=51ZudS1bKSM")
        await self.play_youtube(message, "https://www.youtube.com/watch?v=gWzd1oMggSA")

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

        channel = message.channel
        text = message.content

        # if text.startswith('$j'):
        #     vc = message.author.voice.channel
        #     liveVc = await vc.connect()
        #     await channel.send("Joining voice")
        if text.startswith('$s'):
            if self.__player is not None:
                self.__player.stop()  # Lets the player run it's after callback method.

        elif text.startswith('$p'):
            if len(message.content.split(" ")) > 1:
                youtube_url = message.content.split(" ")[1]
                print(youtube_url)

                await self.play_youtube(message, youtube_url)
            else:
                await channel.send("Please provide a YouTube URL after the '!play' command.")

        elif text.startswith('$history'):
            songRequestHistory = self.__db.get_users_recent_requests(message.author.id)

        elif text.startswith('$allhistory'):
            allHistory = self.__db.get_guild_history_recent()
            await self.display_play_history(message)

        elif text.startswith('$queue'):
            await self.display_queue(message)

    async def play_youtube(self, message, youtube_url: str) -> bool:
        if self.__player is not None:
            # already playing.
            print("Player was already playing.. Appending to queue")

            self.__queue.append((message, youtube_url))  # add to queue
            await message.channel.send("Added your Url to queue!")
        else:
            # not playing
            await self.play_audio(message, youtube_url)

    async def next_song(self):
        if (len(self.__queue) > 0):
            message, youtube_url = self.__queue.pop()
            if self.__player is not None:
                self.__player.stop()
            await message.channel.send("Play song from Queue!")

            await self.play_audio(message, youtube_url)
        else:
            # empty queue
            print("End of queue.")
            pass

    async def stop_youtube(self):
        self.__player.stop()
        self.__player = None

    def on_audio_end(self, error, message):
        print("Error:", str(error))
        if error:
            print(f"Audio playback error: {error}")

        # Play the next song in the queue
        self.loop.create_task(self.next_song())

    async def play_audio(self, message, youtube_url):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                embed = discord.Embed(title='Searching...', description=f'Query: {youtube_url}',
                                      color=discord.Color.yellow())
                botReply = await message.channel.send(embed=embed)
                info_dict = ydl.extract_info(youtube_url, download=True)
                url = None
                songTitle = None
                if 'entries' in info_dict:
                    # For playlists or multiple videos in the search result
                    url = info_dict['entries'][0]['url']
                    song_title = info_dict['entries'][0]['title']
                    filepath = info_dict.get('filepath')

                else:
                    # For single videos
                    url = info_dict['url']
                    song_title = info_dict['title']

                audio_source = discord.FFmpegPCMAudio(url)
                if message.guild.voice_client is None:
                    await message.channel.send("I'm not in a voice channel! Make me join first! (!join)")
                    return
                else:
                    # assign voice_client.
                    self.__player = message.guild.voice_client

                message.guild.voice_client.play(audio_source, after=lambda e: self.on_audio_end(e, message))
                playingEmbed = discord.Embed(description=f'Playing: {song_title}', color=discord.Color.blue())

                await botReply.edit(embed=playingEmbed)

                # Now add to music_database.
                guildID = message.guild.id
                userID = message.author.id
                # Write comments
                self.__db.add_song_request(userID, guildID, song_title, youtube_url)

                # ... (rest of your audio playback code)
            except Exception as e:
                print(f"Search error: {e}")
                await message.channel.send("An error occurred while searching for the video.")

    async def display_queue(self, message):
        if len(self.__queue) > 0:
            i = 1
            embed = discord.Embed(title="Current Queue", color=discord.Color.green())
            for (tempMessage, youtube_url) in self.__queue:
                if (i == 1):
                    embed.add_field(name=f"Next Up",
                                    value=f"**Added by:** {tempMessage.author}\n**URL:** {youtube_url}", inline=False)
                else:
                    embed.add_field(name=f"Position {i}",
                                    value=f"**Added by:** {tempMessage.author}\n**URL:** {youtube_url}", inline=False)
                i += 1
            await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(description="The queue is empty!", color=0xff0000)
            await message.channel.send(embed=embed)

    async def display_play_history(self, message):
        embed = discord.Embed(title="Youtube Search History", color=discord.Color.blurple(), )
        result = self.__db.get_users_recent_requests(message.author.id)
        for i in range(min(len(result), 5)):
            v = result[i]
        date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        # embed.add_field(name="Timestamp", value=)

        await message.channel.send(embed=embed)
        pass


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

# Run the bot with the token
client.run(TOKEN)
