import discord
from discord.ext import commands
from collections import *
import datetime
from main import YDL_OPTS
import yt_dlp
from database import MusicDatabase
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from main import SPOTIFY_CLIENT_ID
from main import SPOTIFY_CLIENT_SECRET


class Music(commands.Cog):
    __slots__ = ["__queue", "__player", "__openai", "__db"]

    def __init__(self, bot):
        self.__player = None
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.__db = MusicDatabase()

        #Get the guild
        guild = self.bot.get_guild(1205275048387285042)

        if guild is None:
            print("The guild was not found!")
            return
        self.__queue = deque()
        self.__player = None  # the voice_client.
        await guild.get_channel(1205275052266889316).connect()
        general = guild.get_channel(1205275051025506318)

        print("The bot is online!")

        # await self.play_youtube(message, "https://www.youtube.com/watch?v=NTbFn09LLuE")
        # await self.play_youtube(message, "https://www.youtube.com/watch?v=51ZudS1bKSM")
        # await self.play_youtube(message, "https://www.youtube.com/watch?v=gWzd1oMggSA")

    @commands.command(description="Play a video from youtube.")
    async def play(self, ctx) -> bool:
        split = ctx.message.content.split(" ")
        channel = ctx.message.channel
        if len(split) > 1:
            orig_url = split[1]
            youtube_url = split[1]
            spotify = False
            if "spotify" in youtube_url:
                spotify = True
                print("Spotify URL detected.")
                youtube_url = await self.get_youtube_url_from_spotify(youtube_url)

            if self.__player is not None:
                # player is active, so we will add to queue instead.
                self.__queue.append((ctx.message, youtube_url))  # add to queue
                # send embed
                embed = discord.Embed(title="Song added to queue", description=f"**Added by:** {ctx.message.author}\n** **[<:YouTube:1208667871291641868> Youtube](youtube_url)", color=discord.Color.darker_gray())
                await channel.send(embed=embed)

            else:
                # Start playing audio.
                if spotify:
                    await self.play_audio(ctx.message, youtube_url, orig_url)
                else:
                    await self.play_audio(ctx.message, youtube_url)
        else:
            await ctx.channel.send("Please provide a YouTube URL after the '!play' command.")

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

    # Write a pause command
    @commands.command(name="pause")
    async def pause(self, ctx):
        if self.__player is not None:
            self.__player.pause()
        else:
            print("No song was playing!")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if self.__player is not None:
            self.__player.stop()
        else:
            print("No song was playing!")

    async def play_youtube(self, message, youtube_url: str) -> bool:
        if self.__player is not None:
            # already playing.
            self.__queue.append((message, youtube_url))  # add to queue
            await message.channel.send("Added your Url to queue!")
        else:
            # not playing
            await self.play_audio(message, youtube_url)

    async def stop_youtube(self):
        self.__player.stop()
        self.__player = None


    async def get_youtube_url_from_spotify(self, spotify_url):
        # Set up the Spotify client
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # Get the track details
        results = sp.track(spotify_url)
        track_name = results['name']
        artist_name = results['artists'][0]['name']

        # Search for the song on YouTube
        youtube_url = await self.search_youtube(f"{track_name} {artist_name}")

        return youtube_url

    # Searches youtube with a query. Returns the first shortened youtube url video.
    async def search_youtube(self, query):
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info_dict = ydl.extract_info(query, download=False)
            video_id = None
            if 'entries' in info_dict:
                # For playlists or multiple videos in the search result
                video_id = info_dict['entries'][0]['id']
            else:
                # For single videos
                video_id = info_dict['id']
            short_url = f"https://youtu.be/{video_id}"
            print(short_url)
            return short_url

    
    def on_audio_end(self, error, message):
        print("Error:", str(error))
        if error:
            print(f"Audio playback error: {error}")

        # Play the next song in the queue
        self.loop.create_task(self.next_song())

    async def play_audio(self, message, youtube_url, spotify_url=None):
        if self.__player is not None:
            self.__player = None
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
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
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn -b:a 192k',
                }
                audio_source = discord.FFmpegPCMAudio(url, before_options=ffmpeg_options['before_options'], options=ffmpeg_options['options'])

                # check if in voice channel
                if message.author.voice is None:
                    voice_channel = message.author.voice.channel
                    await voice_channel.connect()
                    print("Joining voice channel")
                    return

                message.guild.voice_client.play(audio_source, after=lambda e: self.on_audio_end(e, message))
                self.__player = message.guild.voice_client
                if spotify_url is not None:
                    playingEmbed = discord.Embed(description=f':microphone2: Playing: {song_title}\n[[<:SpotifyLogo:1208667871291641868>]({spotify_url})] [[<:YouTube:1208667871291641868> Youtube]({url})]', color=discord.Color.blue())
                else:
                    playingEmbed = discord.Embed(description=f':microphone2: Playing: {song_title}[[<:YouTube:1208667871291641868>({url})]', color=discord.Color.blue())

                await botReply.edit(embed=playingEmbed)

                guildID = message.guild.id
                userID = message.author.id
                # Write comments
                self.__db.add_song_request(userID, guildID, song_title, youtube_url, spotify_url=spotify_url)

            except Exception as e:
                print(f"Search error: {e}")
                await message.channel.send("An error occurred while searching for the video.")


    # Write a volume command
    @commands.command(name="volume")
    async def change_volume(self, message):
        split = message.content.split(" ")
        if len(split) > 1:
            volume = float(split[1])
            if self.__player is not None:
                self.__player.source = discord.PCMVolumeTransformer(self.__player.source, volume)
                await message.channel.send(f"Changed volume to {volume}")
            else:
                await message.reply("No song is currently playing.")
        else:
            await message.channel.send("Please provide a volume level after the '!volume' command.")



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

    # Create a method that prints the most recent 5 songs in the database, as well as how long ago they were played
    @commands.command(name="recent")
    async def display_recent_songs(self, ctx):
        print("Recent")
        guildID = ctx.message.guild.id
        print(guildID)
        recent_songs = self.__db.get_guild_history_recent(guildID)
        print(recent_songs)
        embed = discord.Embed(title="Recent Songs", color=discord.Color.green())
        for song in recent_songs:
            print(song)
            embed.add_field(name=f"Song: {song[0]}", value=f"Played {song[1]}", inline=False)
        await ctx.message.channel.send(embed=embed)


    # Write a new command that prints the user's play history, like the amount of songs they've played
    @commands.command(name="playcount")
    async def display_play_count(self, message):
        userID = message.author.id
        guildID = message.guild.id
        play_count = self.__db.get_play_count(userID, guildID)
        embed = discord.Embed(title="Play Count", color=discord.Color.green())
        embed.add_field(name=f"User: {message.author}", value=f"Play Count: {play_count}", inline=False)
        await message.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
