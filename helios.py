import discord
from discord.ext import commands
from pathlib import Path

bot.remove_command('help')

class Helios(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".")
        self._cogs = [path.stem for path in Path("./Cogs").glob("*.py")]
    
    def load_cogs(self):    
        print("Loading cogs")
        for cog in self._cogs:
            self.load_extension(f"Cogs.{cog}")
            print(f"{cog} commands have been loaded")
        print("All cogs Loaded")

    def run(self):
        self.load_cogs()
        with open("./t0ken", "r", encoding="utf-8") as f:
            TOKEN = f.read()
        super().run(TOKEN, reconnect= True)
    
    async def on_ready(self):
        await self.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('Jammin to music'))
        print("{0} has sucessfully connected to Discord".format(bot.user))
    

bot = Helios()
bot.run()