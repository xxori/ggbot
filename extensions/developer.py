import discord
from discord.ext import commands
import asyncio
import datetime
import random
import subprocess

# helpful functions
import utils


class Developer(discord.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @property
    def description(self):
        return "Developer-related commands. Devs only."

    @utils.is_leader()
    @commands.command(
        brief="Reloads a cog (for developer use only)",
        usage="[cog]",
        aliases=["rl", "rload"],
        hidden=True,
    )
    async def reload(self, ctx, cog):
        self.bot.reload_extension(f"extensions.{cog}")
        self.bot.logger.info(
            f"Cog {cog} reloaded by {ctx.message.author} ({ctx.message.author.id})"
        )
        await ctx.send(f":thumbsup: Extension ``{cog}`` successfully reloaded")

    @utils.is_leader()
    @commands.command(brief="Die bitch", aliases=["die", "fuckoff"], hidden=True)
    async def suicide(self, ctx):
        await ctx.send(":weary::gun: Farewell...")
        if ctx.message.guild:
            self.bot.logger.info(
                f"Bot terminated from {ctx.message.guild} ({ctx.message.guild.id}) by {ctx.message.author} ({ctx.message.author.id})"
            )
        else:
            self.bot.logger.info(
                f"Bot terminated from dms by {ctx.message.author} ({ctx.message.author.id})"
            )
        self.bot.logger.info("Bot has shut down successfully.")
        await self.bot.logout()

    @utils.is_leader()
    @commands.command(brief="Update presences rotation", hidden=True)
    async def updatepres(self, ctx):
        self.bot.presence_looping = False
        self.bot.loop.create_task(self.bot.presence_changer())
        await ctx.send(":thumbsup: Presence loop restarted.")

    @utils.is_leader()
    @commands.command(brief="Loads an extension", usage="[cog]", hidden=True)
    async def load(self, ctx, cog):
        self.bot.load_extension(f"extensions.{cog}")
        self.bot.logger.info(
            f"Cog {cog} loaded by {ctx.message.author} ({ctx.message.author.id})"
        )
        await ctx.send(f":thumbsup: Extension ``{cog}`` successfully loaded")

    @utils.is_leader()
    @commands.command(
        brief="Unloads a loaded extension",
        aliases=["uload"],
        usage="[cog]",
        hidden=True,
    )
    async def unload(self, ctx, cog):
        self.bot.unload_extension(f"extensions.{cog}")
        self.bot.logger.info(
            f"Cog {cog} unloaded by {ctx.message.author} ({ctx.message.author.id})"
        )
        await ctx.send(f":thumbsup: Extension ``{cog}`` successfully loadn't")


def setup(bot):
    bot.add_cog(Developer(bot))
