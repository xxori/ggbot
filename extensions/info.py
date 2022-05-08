import discord
from discord.ext import commands, bridge
import time
import datetime


class Utility(discord.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @bridge.bridge_command(name="ping", description="Get bot latency")
    async def ping(self, ctx):
        text = "Websocket: `{:.2f}ms`\nLatency: `...`".format(self.bot.latency * 1000)
        start = time.perf_counter()
        msg = await ctx.respond(text)
        end = time.perf_counter()

        if isinstance(msg, discord.Interaction):
            await msg.edit_original_message(
                content=text.replace("...", "{:.2f}ms".format((end - start) * 1000))
            )
        else:
            await msg.edit(text.replace("...", "{:.2f}ms".format((end - start) * 1000)))

    @bridge.bridge_command(name="info", description="Get Club Info")
    async def info(self, ctx):
        embed = discord.Embed(
            color=self.bot.emb_color, timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="GIHS Gaming+ Club")
        embed.add_field(
            name="Club Captains",
            value="Martin: "
            + ctx.guild.get_member(304219290649886720).mention
            + "\nIsaac: "
            + ctx.guild.get_member(348024578901147648).mention
            + "\nXun: "
            + ctx.guild.get_member(544809984303562752).mention,
            inline=False,
        )
        embed.add_field(
            name="Club Meetings",
            value="3HS04 & 3HS05 every Tuesday at lunch time",
            inline=False,
        )
        embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.respond(embed=embed)

    @property
    def description(self):
        return "Useful commands to provide information"


def setup(bot):
    bot.add_cog(Utility(bot))
