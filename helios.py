import discord
import options
from discord.ext import commands
from pathlib import Path
import asyncio

class Helios(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=".", intents=intents)
        self._cogs = [path.stem for path in Path("./Cogs").glob("*.py")]
    
    async def load_cogs(self):    
        print("Loading cogs")
        for cog in self._cogs:
            if cog not in  ["options", "Utility"]:
                await self.load_extension(f"Cogs.{cog}")
                print(f"{cog} commands have been loaded")
        print("All cogs Loaded")

    #async def run(self):
     #   await self.load_cogs()
     #   await super().run(options.DISCORD_TOKEN, reconnect= True)
    
    async def on_ready(self):
        await self.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('Smurfin in diamond lobbies'))
        print("{0} has sucessfully connected to Discord".format(bot.user))
    


bot = Helios()
bot.remove_command('help')
asyncio.run(bot.load_cogs())
asyncio.run(bot.run(options.DISCORD_TOKEN, reconnect= True))
#bot.run()