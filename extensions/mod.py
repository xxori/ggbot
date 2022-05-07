import discord
from discord.ext import bridge,commands
import utils

class Moderation(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @property
    def description(self):
        return "Moderation-related commands"
    
    
    @commands.check(utils.is_leader)
    @bridge.bridge_command(name="send", aliases=["s"], description="DM a server member")
    async def send(self, ctx,member: discord.Member,*,message:str):
        if member.dm_channel is None:
            dm = await member.create_dm()
        else:
            dm = member.dm_channel
        
        await dm.send("ADMIN: " + message)
        await ctx.reply(message + " -> " + member.mention)

def setup(bot):
    bot.add_cog(Moderation(bot))