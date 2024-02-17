import discord
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online!")

    @commands.Command
    async def ping(self, ctx):
        await ctx.send("Pong")


async def setup(bot):
    await bot.add_cog(Ping(bot))