import discord
from discord.ext import commands
from collections import *
import datetime
from main import YDL_OPTS
import yt_dlp
from database import MusicDatabase


class Music(commands.Cog):
    __slots__ = ["__queue", "__player", "__openai", "__db"]

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Other startup!")
        self.__db = MusicDatabase()
        print("Other startup2!")

        #Get the guild
        guild = self.bot.get_guild(1205275048387285042)

        if guild is None:
            print("The guild was not found!")
            return
        self.__queue = deque()
        self.__player = None  # the voice_client.
        await guild.get_channel(1205275052266889316).connect()
        channel = guild.get_channel(1205275051025506318)
        message = await channel.send("Joining voice")
        print("Other startup3!")

        await self.play_youtube(message, "https://www.youtube.com/watch?v=NTbFn09LLuE")
        await self.play_youtube(message, "https://www.youtube.com/watch?v=51ZudS1bKSM")
        await self.play_youtube(message, "https://www.youtube.com/watch?v=gWzd1oMggSA")

    @commands.command(description="Play a video from youtube.")
    async def play(self, ctx) -> bool:
        print("Playing video from")
        #  message, youtube_url: str
        if len(ctx.message.content.split(" ")) > 1:
            youtube_url = ctx.message.content.split(" ")[1]

            if self.__player is not None:
                # already playing.
                print("Player was already playing.. Appending to queue")

                self.__queue.append((ctx.message, youtube_url))  # add to queue
                await ctx.message.channel.send("Added your Url to queue!")
            else:
                # not playing
                await self.play_audio(ctx.message, youtube_url)
        else:
            await ctx.channel.send("Please provide a YouTube URL after the '!play' command.")
        ctx.message.delete()

    async def play_youtube(self, message, youtube_url: str) -> bool:
        print("play_youtube")
        if self.__player is not None:
            # already playing.
            print("Player was already playing.. Appending to queue")

            self.__queue.append((message, youtube_url))  # add to queue
            await message.channel.send("Added your Url to queue!")
        else:
            # not playing
            print("Not playing")
            await self.play_audio(message, youtube_url)

    async def stop_youtube(self):
        self.__player.stop()
        self.__player = None

    @commands.command(name="next")
    async def next(self, ctx):
        if len(self.__queue) > 0:
            message, youtube_url = self.__queue.pop()
            if self.__player is not None:
                self.__player.stop()
            await message.channel.send("Play song from Queue!")

            await self.play_audio(message, youtube_url)
        else:
            # empty queue
            print("End of queue.")
            pass

    @commands.command(name="stop")
    async def stop(self, ctx):
        if self.__player is not None:
            self.__player.stop()
            self.__player = None
        else:
            print("No song was playing!")

    def on_audio_end(self, error, message):
        print("Error:", str(error))
        if error:
            print(f"Audio playback error: {error}")

        # Play the next song in the queue
        self.loop.create_task(self.next_song())

    async def play_audio(self, message, youtube_url):
        print(message)
        print(youtube_url)
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            print("Here")
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
                print("Here2")

                if message.guild.voice_client is None:
                    await message.channel.send("I'm not in a voice channel! Make me join first! (!join)")
                    return
                else:
                    # assign voice_client.
                    self.__player = message.guild.voice_client

                message.guild.voice_client.play(audio_source, after=lambda e: self.on_audio_end(e, message))
                playingEmbed = discord.Embed(description=f'Playing: {song_title}', color=discord.Color.blue())

                await botReply.edit(embed=playingEmbed)

                guildID = message.guild.id
                userID = message.author.id
                # Write comments
                self.__db.add_song_request(userID, guildID, song_title, youtube_url)

            except Exception as e:
                print(f"Search error: {e}")
                await message.channel.send("An error occurred while searching for the video.")

    async def next_song(self):
        if len(self.__queue) > 0:
            message, youtube_url = self.__queue.pop()
            await self.play_audio(message, youtube_url)
        else:
            print("End of queue.")

    @commands.command(name="queue")
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


async def setup(bot):
    await bot.add_cog(Music(bot))
