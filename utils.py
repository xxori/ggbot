import datetime
from  bot import read_config
from discord.ext import commands

cfg = read_config()

def is_leader():
    async def predicate(ctx):
        if ctx.author.id not in cfg["club_leaders"]:
            raise NotLeader()
        return True

    return commands.check(predicate)

def get_club():
    return cfg["club_guild"]

class HierarchyPermissionError(commands.CommandError):
    def __init__(self, ctx, target):
        super().__init__('', [ctx, target])

class NotLeader(commands.CheckFailure):
    pass