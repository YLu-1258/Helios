import discord
import asyncio
from options import Music_CMDS
from discord.ext import commands
from discord.utils import get

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True, brief = 'help command', aliases = ["h"])
    async def help(self, ctx):
            embed1 = discord.Embed(title="Help Command", description=Music_CMDS, color=0x0000ff)
            embed1.set_footer(text="Called by: {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed1)
            
def setup(bot):
    bot.add_cog(Help(bot))