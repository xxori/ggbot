import discord
from discord.ext import commands, bridge
import time

class Utility(discord.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @bridge.bridge_command(name="ping", description="Get bot latency")
    async def ping(self, ctx):
        text = "Websocket: `{:.2f}ms`\nLatency: `...`".format(self.bot.latency*1000)
        start = time.perf_counter()
        msg = await ctx.respond(text)
        end = time.perf_counter()
        await msg.edit(text.replace("...","{:.2f}ms".format((end-start)*1000)))


    @property
    def description(self):
        return 'Useful commands to provide information'



def setup(bot):
    bot.add_cog(Utility(bot))