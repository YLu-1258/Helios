import discord
import asyncio
from discord.ext import commands
from discord.utils import get
from discord_ui import UI, SelectMenu, SelectOption

Music_CMDS = "```yaml\n .join ```\nMakes the music bot join the caller's voice channel\n\nAlternatives: `.joi, .j`\n\n" + "```yaml\n .leave ```\nMakes the music bot leave the caller's voice channel\n\nAlternatives: `.l `\n\n" + "```yaml\n .play {song} ```\nPlays or queues requested song\n\n__Song Options__\n- Request a song by typing the name of it\n- Provide a Youtube url\n\nAlternatives: `.p, .paly, .pl`\n\n"


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True, brief = 'Pseudo-help command', aliases = ["pseudo"])
    async def phelp(self, ctx):
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
    bot.add_cog(Test(bot))
    ui = UI(bot)