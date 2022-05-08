import discord
from discord.ext import bridge, commands
import utils


class Moderation(discord.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @property
    def description(self):
        return "Moderation-related commands"

    @utils.is_leader()
    @commands.command(
        name="send", aliases=["s"], description="DM a server member", hidden=True
    )
    async def send(self, ctx, member: discord.Member, *, message: str):
        if member.dm_channel is None:
            dm = await member.create_dm()
        else:
            dm = member.dm_channel

        await dm.send("Admin: " + message)
        await ctx.message.add_reaction("✅")

    @utils.is_leader()
    @commands.command(
        brief="Execute command as another user.", usage="[user] <command>", hidden=True
    )
    async def sudo(self, ctx, user: discord.Member, *, cmd):
        # Command name taken from the unix command sudo

        await ctx.send(f"Sudoing ``{cmd}`` as ``{user}``.")

        # Creates new context object using modified parameters
        sudo_msg = ctx.message
        sudo_msg.author = user
        sudo_msg.content = ctx.prefix + cmd.replace(ctx.prefix, "", 1)
        sudo_ctx = await self.bot.get_context(sudo_msg)
        # Invokes new context
        await self.bot.invoke(sudo_ctx)


def setup(bot):
    bot.add_cog(Moderation(bot))
