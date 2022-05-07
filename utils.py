import datetime
from  bot import read_config

def is_leader(ctx):
    cfg = read_config()
    return ctx.author.id in cfg["club_leaders"]

def get_club():
    cfg = read_config()
    return cfg["club_guild"]

