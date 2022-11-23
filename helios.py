import discord
import options
from discord.ext import commands
from pathlib import Path

class Helios(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", help_command=None)
        self._cogs = [path.stem for path in Path("./Cogs").glob("*.py")]
    
    def load_cogs(self):    
        print("Loading cogs")
        for cog in self._cogs:
            if cog not in  ["options", "Utility", "pafy", "youtube_dl", "spotipy", "redis", "packaging", "lyricsgenius", "bs4", "nacl", "discord"]:
                self.load_extension(f"Cogs.{cog}")
                print(f"{cog} commands have been loaded")
        print("All cogs Loaded")

    def run(self):
        self.load_cogs()
        super().run(options.DISCORD_TOKEN, reconnect= True)
    
    async def on_ready(self):
        await self.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('Smurfin in diamond lobbies'))
        print("{0} has sucessfully connected to Discord".format(bot.user))
    

bot = Helios()
bot.remove_command('help')
bot.run()