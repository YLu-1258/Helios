import discord
import asyncio
from options import Music_CMDS
from discord.ext import commands
from discord.utils import get
from discord_ui import UI, SelectMenu, SelectOption

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True, brief = 'Pseudo-help command', aliases = ["h"])
    async def help(self, ctx):
        embed = discord.Embed(title="Help Command", description="Please select from the following options", color=0x0000ff)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Called by: {0}".format(ctx.author.display_name))
        msg = await ctx.send(embed=embed, components=[SelectMenu(options=[SelectOption("0", label="Music", description="Grabs music commands"), SelectOption("1", label = "Moderation", description="Server Moderation commands")], max_values=1)])
        try:
            sel = await msg.wait_for("select", self.bot, by=ctx.author, timeout=5)
            u_ipt = str([x.content for x in sel.selected_options][0])
            if u_ipt == "Music":
                desc = Music_CMDS
            embed1 = discord.Embed(title="Help Command", description=desc, color=0x0000ff)
            embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed1.set_footer(text="Called by: {0}".format(ctx.author.display_name))
            await msg.edit(embed=embed1, components=[SelectMenu(options=[SelectOption("0", label="Music", description="Grabs music commands"), SelectOption("1", label = "Moderation", description="Server Moderation commands")], max_values=1)])
        except asyncio.exceptions.TimeoutError:
            await msg.delete()
            
def setup(bot):
    bot.add_cog(Help(bot))
    ui = UI(bot)