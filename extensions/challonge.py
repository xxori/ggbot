import challonge
import discord
from discord.ext import bridge, commands
import utils
import asyncio
import re
import orjson
import os

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
        hidden=True,
    )
    @utils.is_leader()
    async def tournament(self, ctx):
        await self.list(ctx)

    @tournament.command(brief="List ongoung tournaments", hidden=True)
    @utils.is_leader()
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

    @tournament.command(brief="Registers a user to a tournament", hidden=True)
    @utils.is_leader()
    async def register(
        self,
        ctx,
        id: int,
        name: str,
        mentor_group: int,
        discord_user: discord.Member,
        email: str,
    ):
        name = name.replace("_", " ")
        nshortened = getshortname(name)
        if id in self.bot.tournaments.keys():
            if nshortened in self.bot.tournaments[id].keys():
                return await ctx.send("That user is already in the tournament bro")

        if id not in self.bot.tournaments.keys():
            self.bot.tournaments[id] = {}
        self.bot.tournaments[id][nshortened] = {
            "name": name,
            "mentor_group": mentor_group,
            "discord_id": discord_user.id,
            "email": email,
        }
        await ctx.send("User added")
        await self.update_participants(ctx, id)

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

    @tournament.command(brief="Updates tournament users to challonge")
    @utils.is_leader()
    async def update_participants(self, ctx, id: int):
        names = list(self.bot.tournaments[id].keys())

        namesin = [i["name"] for i in challonge.participants.index(id)]

        names = set(names) ^ set(
            namesin
        )  # Getting names that aren't already in challonge through some cool xor

        if len(names) == 0:
            await ctx.send("No new participants to be registered")
        else:
            challonge.participants.bulk_add(id, names)
            await ctx.send("Participants successfully registered")

        r = challonge.participants.index(id)
        users = self.bot.tournaments[id]
        for participant in r:
            for user in users.keys():
                if not participant["name"] or not users[user]["name"]:
                    continue
                if participant["name"].lower() == user.lower():
                    users[user]["challonge_pid"] = participant["id"]

        await ctx.send("Participant ids updated")

    @tournament.command(
        brief="Start a tournament (This will alter the server hierarchy and add multiple users to the tournament channels)"
    )
    @utils.is_leader()
    async def start(self, ctx, id: int):
        await ctx.send(
            "Are you sure you want to start this tournament? This will create a channel for each match and add the users (type confirm)"
        )

        def check(m):
            return m.author == ctx.author

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=10.0)
        except asyncio.TimeoutError:
            return await ctx.send("You timed out, please try again")

        if msg.content.lower() != "confirm":
            return await ctx.send("Tournament init cancelled")

        await ctx.send("Updating participant ids")
        await self.update_participants(ctx, id)

        await ctx.send("Starting tournament using API")
        if challonge.tournaments.show(id)["state"] != "underway":
            challonge.tournaments.start(id)
        await ctx.send("Creating match channels")

        matches = challonge.matches.index(id, state="open")
        for match in matches:
            p1id = match["player1_id"]
            p1 = None

            p2id = match["player2_id"]
            p2 = None

            for player in self.bot.tournaments[id].values():
                if p1id == player["challonge_pid"]:
                    p1 = player
                if p2id == player["challonge_pid"]:
                    p2 = player

            if p1 is None or p2 is None:
                return await ctx.send("Players not found")

            guild = self.bot.guild
            m1 = guild.get_member(p1["discord_id"])
            m2 = guild.get_member(p2["discord_id"])

            overrides = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                m1: discord.PermissionOverwrite(
                    read_messages=True, read_message_history=True, send_messages=True
                ),
                m2: discord.PermissionOverwrite(
                    read_messages=True, read_message_history=True, send_messages=True
                ),
            }

            channel = await self.bot.tourncategory.create_text_channel(
                f"{getshortname(p1['name'])} vs {getshortname(p2['name'])}",
                reason="Automatic tournament generation",
                topic=str(id)+"-"+str(match["id"]),
                overwrites=overrides,
            )
            await channel.send(f"{m1.mention} vs {m2.mention}. among us")
        await ctx.send("Done")

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
    
    @bridge.bridge_command(brief="Reports score for a tournament game (Format X-Y where X is your score and Y is opponents)")
    async def report(self,ctx,score:str):
        if ctx.channel.category != self.bot.tourncategory:
            return await ctx.respond("This command can only be used in tournament channels")
        
        if len(score.split("-")) != 2 or not score.split("-")[0].isdigit() or not score.split("-")[1].isdigit():
            return await ctx.respond("Please report match score in format X-Y where x is your score and y is the opponents score as numbers")
        
        tournid = int(ctx.channel.topic.split("-")[0])
        matchid = int(ctx.channel.topic.split("-")[1])
        match = challonge.matches.show(tournid,matchid)
        if match["state"] != "open":
            return await ctx.respond("Reporting is not currently allowed on this match")
        p1id = match["player1_id"]
        p1 = None

        p2id = match["player2_id"]
        p2 = None

        for player in self.bot.tournaments[tournid].values():
            if p1id == player["challonge_pid"]:
                p1 = player
            if p2id == player["challonge_pid"]:
                p2 = player

        if p1 is None or p2 is None:
            return await ctx.respond("Something went wrong. Please contact admins")
        
        m1 = ctx.guild.get_member(p1["discord_id"])
        m2 = ctx.guild.get_member(p2["discord_id"])

        if ctx.author not in [m1,m2]:
            return await ctx.respond("You are not a participant in this match")

        if m1 is None or m2 is None:
            return await ctx.respond("Something went wrong. Please contact admins")
        
        if ctx.author.id == p2["discord_id"]:
            score = score.split("-")[1] + "-" + score.split("-")[0]
            othermem = m1
        else:
            othermem = m2
        
        if int(score.split("-")[0]) > int(score.split("-")[1]):
            winner = m1
            winnerid = p1["challonge_pid"]
        elif int(score.split("-")[1]) > int(score.split("-")[0]):
            winner = m2
            winnerid = p2["challonge_pid"]
        else:
            return await ctx.respond("Something went wrong. Please contacta dmins")
        
        await ctx.respond("Successfully reported")
        await ctx.send(f"Pending score {score} with {winner.mention} winning. Please type 'confirm' to confirm these results or anything else to deny them {othermem.mention}. Anyone else may also type 'cancel' to cancel score submission")
        
        def check(m):
            return m.content.lower() == 'cancel' or m.author == othermem

        try:
            m = await self.bot.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            return await ctx.send("Confirmation timed out, try again")
        
        if m.content.lower() == "cancel" or (m.author == othermem and m.content.lower() != "confirm"):
            return await ctx.send("Score submission cancelled, try again")
        
        challonge.matches.update(tournid,matchid,scores_csv=score,winner_id=winnerid)
        await ctx.send("Score successfully updated")



def check_cancel(arg):
    return arg.lower() == "cancel"


def getshortname(name):
    return name.split(" ")[0] + " " + name.split(" ")[1][0]


def setup(bot):
    if "challonge_api_key" in bot.config.keys():
        bot.add_cog(Challonge(bot))
