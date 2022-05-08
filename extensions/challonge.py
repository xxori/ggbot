import challonge
import discord
from discord.ext import bridge, commands
import utils
import asyncio
import re

URL_CONDITION = re.compile(r"^[A-Za-z0-9_]*$")


class Challonge(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        challonge.set_credentials(
            bot.config["challonge_username"], bot.config["challonge_api_key"]
        )

    @commands.group(
        invoke_without_command=True,
        brief="Category with commands relating to Challonge tournaments",
        usage="[subcommand] <arguments>",
    )
    @utils.is_leader()
    async def tournament(self, ctx):
        await self.list(ctx)

    @tournament.command(brief="List ongoung tournaments")
    async def list(self, ctx):
        msg = await ctx.send("Fetching...")
        tourneys = challonge.tournaments.index()
        if len(tourneys) == 0:
            return await ctx.send(
                "No ongoing tournaments for ``" + challonge.get_credentials()[0] + "``"
            )

        await msg.edit(
            "\n".join(
                [f"{t['id']}-{t['name']}-{t['full_challonge_url']}" for t in tourneys]
            )
        )

    @tournament.command(
        brief="Show a specific tournament going on", usage="[tournament id]"
    )
    @utils.is_leader()
    async def show(self, ctx, id: int):
        msg = await ctx.send("Fetching...")
        try:
            t = challonge.tournaments.show(id)
        except:
            return await ctx.send("Invalid tournament id")

        id = t["id"]
        del t["id"]
        # args = f"Name: {t['name']}\nURL: https://challonge.com/{t['url']}\n"+(t['description'] if t['description'] else "")+f"Type: {t['tournament_type']}\nState: {t['state']}\nOpen Signup: "
        args = ""
        for k, v in t.items():
            if v == "" or v is None:
                continue
            if v is True:
                args += f"{k}: Yes\n"
            elif v is False:
                args += f"{k}: No\n"
            else:
                args += f"{k}: {v}\n"
        await msg.edit(
            "Full schema found at <https://api.challonge.com/v1/documents/tournaments/show>\n```"
            + args
            + "```"
        )

    @tournament.command(
        brief="Updates a tournament parameter",
        usage="[tourament id] <parameter> <value>",
    )
    @utils.is_leader()
    async def update(self, ctx, id: int, param, value):
        msg = await ctx.send("Setting...")
        try:
            challonge.tournaments.update(id, **{param: value})
            await msg.edit("Updating tournament ``" + str(id) + "`` success")
        except:
            await msg.edit("Updating tournament ``" + str(id) + "`` failed")

    @tournament.command(brief="Initiates the tournament creation wizard")
    @utils.is_leader()
    async def create(self, ctx):
        await ctx.send(
            f"Initiating tournament creation for user `{challonge.get_credentials()[0]}`, type cancel at any time to abort"
        )
        params = {}
        name = ""
        url = ""
        tournament_type = ""
        try:
            await ctx.send("Please send tournament name[string]")

            def check(m):
                return m.author == ctx.author and (
                    len(m.content) < 60 or m.content.lower() == "cancel"
                )

            message = await self.bot.wait_for("message", check=check, timeout=20.0)
            name = message.content

            await ctx.send(
                "Please send tournament url[string with only letters, numbers, underscores]. The tournament will be found at challonge.com/url"
            )

            def check(m):
                return m.author == ctx.author and (
                    bool(re.match(URL_CONDITION, m.content)) is True
                    or m.content.lower() == "cancel"
                )

            message = await self.bot.wait_for("message", check=check, timeout=20.0)
            if check_cancel(message.content):
                return await ctx.send("Successfully cancelled")
            url = message.content

            await ctx.send(
                "Please send tournament type[single elimination, double elimination, round robin, swiss]"
            )

            def check(m):
                return m.author == ctx.author and (
                    m.content.lower()
                    in [
                        "single elimination",
                        "double elimination",
                        "round robin",
                        "swiss",
                    ]
                    or m.content.lower() == "cancel"
                )

            message = await self.bot.wait_for("message", check=check, timeout=20.0)
            if check_cancel(message.content):
                return await ctx.send("Successfully cancelled")
            tournament_type = message.content

            await ctx.send(
                "Please send any additional params, found at https://api.challonge.com/v1/documents/tournaments/create, in form param1=arg,param2=arg,param3=arg. Params that are not set will return to default. Send 'skip' if there are none to set"
            )

            def check(m):
                return m.author == ctx.author

            message = await self.bot.wait_for("message", check=check, timeout=300.0)
            if check_cancel(message.content):
                return await ctx.send("Successfully cancelled")
            if message.content.strip().lower() != "skip":
                pairs = message.content.split(",")
                for pair in pairs:
                    kv = pair.split("=")
                    params[kv[0]] = kv[1]

            await ctx.send(
                f"Tournament Information, type confirm or cancel\nName: {name}\nURL (If a valid tournament shows up then you will have to cancel): https://challonge.com/{url}\nTournament Type: {tournament_type}\nOther Params:\n"
                + "\n".join([f"{k}: {v}" for k, v in params.items()])
            )

            def check(m):
                return m.author == ctx.author and m.content.lower() in [
                    "confirm",
                    "cancel",
                ]

            message = await self.bot.wait_for("message", check=check, timeout=15.0)
            if check_cancel(message.content):
                return await ctx.send("Successfully cancelled")
            try:
                challonge.tournaments.create(name, url, tournament_type, **params)
            except:
                await ctx.send("Tournament creation failed, please retry")
            await ctx.send("Tournament creation successful")

        except asyncio.TimeoutError:
            await ctx.send("You have timed out, please restart")


def check_cancel(arg):
    return arg.lower() == "cancel"


def setup(bot):
    if "challonge_api_key" in bot.config.keys():
        bot.add_cog(Challonge(bot))
