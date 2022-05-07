import discord
from discord.ext import bridge,commands
import traceback
import os
import sys
import datetime
import aiohttp
import utils
import json
import logging
import time

class ggBot(bridge.AutoShardedBot):
    def __init__(self, logger, config):
        super(ggBot, self).__init__(command_prefix=">", intents=discord.Intents.all())
        self.logger = logger
        self.config = config
        self.run_time = None
        self.connect_time = None
        self.module_directories = ["extensions"]

    def is_leader(self, ctx):
        return ctx.author.id in self.config["club_leaders"]

    def load_cogs(self):
        for module_dir in self.module_directories:
            if os.path.isdir(f"./{module_dir}"):
                self.logger.info(f'Loading extensions from "{module_dir}"')
                for module in [
                    i.replace(".py", "", 1)
                    for i in os.listdir(f"./{module_dir}")
                    if i.endswith(".py")
                ]:
                    try:
                        self.load_extension(f"{module_dir}.{module}")
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to load extension {module_dir}.{module}"
                        )
                        traceback.print_exception(type(e), e, e.__traceback__)
                    else:
                        self.logger.info(f"Loaded extension {module_dir}.{module}")
                self.logger.info(f'Finished loading from "{module_dir}"')
        self.logger.info("Finished loading modules.")

    def run(self):
        self.load_cogs()
        self.run_time = datetime.datetime.utcnow()
        self.logger.info("Pre-start checks cleared, start login.")

        try:
            super(ggBot, self).run(self.config["token"].strip())
        except discord.LoginFailure as e:
            self.logger.critical(f"Login Failure - {e} (check your config)")
        except aiohttp.ClientConnectionError as e:
            self.logger.critical(f"Connection Error - {e}")

        runtime = datetime.datetime.utcnow() - self.run_time
        self.logger.info(
            f'Running duration: {datetime.timedelta(seconds=runtime)}'
        )

    async def close(self):
        if hasattr(self, "session"):
            await self.session.close()
        await super().close()
        self.logger.info("Bot has shut down successfully.")
    
        # events
    async def on_message(self, message):
        if self.is_ready:
            ctx = await self.get_context(message)
            if ctx.author == self:
                return
            if ctx.guild is None:
                await self.modmail(ctx)
                return
            if ctx.guild != self.guild:
                return
            
            await super().on_message(message)

    async def on_ready(self):
        old_time = self.connect_time
        self.connect_time = datetime.datetime.utcnow()
        self.logger.info(
            f'Connection time reset. ({old_time or "n/a"} -> {self.connect_time})'
        )
        self.logger.info(f"Client ready: {self.user} ({self.user.id})")

        self.session = aiohttp.ClientSession(loop=self.loop)

        await self.change_presence(activity=discord.Game(name="DM me to message the mods!"))

        self.guild = self.get_guild(self.config["club_guild"])
        if not self.guild:
            self.logger.critical("Bot not a member of the club guild")
            await self.close()
        self.logchannel = self.guild.get_channel(self.config["log_channel"])
        if not self.logchannel:
            self.logger.critical("Logging channel not found")
            await self.close()
        self.mailchannel = self.guild.get_channel(self.config["modmail_channel"])
        if not self.mailchannel:
            self.logger.critical("Modmail channel not found")
            await self.close()

        self.logger.info("Initialization finished.")

    async def log(self, message):
        await self.logchannel.send(
            f"[{datetime.utcnow().strptime('%d/%m/y %H:%M')} UTC] " + str(message)
        )
    
    async def modmail(self, ctx):
        await self.mailchannel.send(f"{ctx.author.mention}-{ctx.author.id}: {ctx.message.content}")


def read_config():
    conf_template = {
        "token": "create an application at https://discordapp.com/developers/",
        "logfiles": {"enabled": False, "overwrite": False},
        "log_channel": -1,
        "club_leaders": [
            -1
        ],  # developers that can execute dev commands
        "club_guild": -1,  # main guild bot operates around, set to -1 to disable
        "log_channel": -1,
        "modmail_channel": -1
    }

    if not os.path.isfile("config.json"):
        with open("config.json", "w+") as f:
            json.dump(conf_template, f, indent=4)
        return conf_template
    else:
        with open("config.json", "r") as f:
            data = json.load(f)
        return data


if __name__ == "__main__":
    config = read_config()

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    stdhandler = logging.StreamHandler()
    stdhandler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] : %(message)s", "%d/%m/%Y %H:%M:%S"
        )
    )
    logger.addHandler(stdhandler)

    if config["logfiles"]["enabled"]:
        if not os.path.isdir("logs"):
            os.mkdir("logs")

        if not config["logfiles"]["overwrite"]:
            date = datetime.datetime.now().strftime("%d-%m-%y")
            lastid = 0
            for filename in os.listdir("logs"):
                if filename.startswith(date):
                    x = int(filename.split(".log")[0].split("#")[-1])
                    lastid = x if x > lastid else lastid
            logfile = f"logs/{date} #{lastid+1}.log"
        else:
            logfile = "logs/latest.log"
        print(f"Logging to {logfile}")

        filehandler = logging.FileHandler(filename=logfile, encoding="utf-8", mode="w")
        filehandler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] : %(message)s", "%d/%m/%Y %H:%M:%S"
            )
        )
        logger.addHandler(filehandler)

    time.sleep(0.1)
    bot = ggBot(logger=logger, config=config)

    bot.run()