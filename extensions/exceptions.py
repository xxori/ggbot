import discord
from discord.ext import commands
import asyncio
import traceback
import utils


class EventHandler(discord.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, e):
        # error parsing & preparations
        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(e, commands.CommandInvokeError):
            e = e.original

        # missing/malformed things
        if isinstance(e, commands.MissingRequiredArgument):
            clean_param = str(e.param).split(":")[0]
            await ctx.send(
                f":x: ``{ctx.command.name}`` requires the ``{clean_param}`` argument!"
            )
            await ctx.send_help(ctx.command.name)

        elif isinstance(e, commands.BadArgument):
            msg = e.args[0].replace('"', "`")
            await ctx.send(f":x: {msg}")
            await ctx.send_help(ctx.command.name)

        elif isinstance(e, commands.CommandNotFound):
            pass  # annoying reactions when randomly typing prefix, removed old code

        # permission errors
        elif isinstance(e, commands.MissingPermissions):
            perm_name = (
                e.args[0]
                .replace("You are missing ", "")
                .replace(" permission(s) to run this command.", "")
                .strip()
            )
            await ctx.send(
                f":closed_lock_with_key: You need ``{perm_name}`` to be able to execute ``{ctx.command.name}``"
            )

        elif isinstance(e, utils.HierarchyPermissionError):
            command = e.args[1][0].command
            target = e.args[1][1]
            await ctx.send(f":x: I am not authorized to {command.name} ``{target}``.")

        elif isinstance(e, commands.BotMissingPermissions):
            perm_name = (
                e.args[0]
                .replace("Bot requires ", "")
                .replace(" permission(s) to run this command.", "")
                .strip()
            )
            await ctx.send(
                f":closed_lock_with_key: I need ``{perm_name}`` to be able to execute ``{ctx.command.name}``"
            )

        elif isinstance(e, discord.Forbidden):
            await ctx.send(f":closed_lock_with_key: I am not authorized to do that.")

        elif isinstance(e, commands.NotOwner):
            await ctx.send(
                f":closed_lock_with_key: ``{ctx.command.name}`` can be executed only by server owner."
            )

        elif isinstance(e, discord.ExtensionAlreadyLoaded):
            await ctx.send(f":x: {e.args[0]}")

        elif isinstance(e, discord.ExtensionNotLoaded):
            await ctx.send(f":x: {e.args[0]}")

        elif isinstance(e, discord.ExtensionNotFound):
            await ctx.send(f":x: ``{e.args[0]}`` does not exist.")

        # uh oh something broke
        elif isinstance(e, discord.HTTPException):
            traceback.print_exception(type(e), e, e.__traceback__)

        elif isinstance(e, utils.NotLeader):
            pass

        elif isinstance(e, commands.CheckFailure):
            # checks should never just return, but instead raise an error to be caught here
            # if a check is still raising this then it's written badly
            # what are you still waiting for, a kiss?
            # go fix it

            # here, let me help you out
            traceback.print_exception(type(e), e, e.__traceback__)
            # there, stop slacking off now
            return

        else:
            # await ctx.send(
            #    f":x: An internal error has occurred. ```py\n{type(e)}: {e}```"
            #)
            await ctx.send(":x: Something went wrong. Contact admins if you expected it to go right")
            traceback.print_exception(type(e), e, e.__traceback__)


def setup(bot):
    bot.add_cog(EventHandler(bot))
