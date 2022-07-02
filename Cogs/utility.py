import discord
from discord.ext import commands

class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, brief='help command', aliases=['h'])
    async def help(self, ctx):
        embed = discord.Embed(title="HELP", description="thingy", color=0xff0000)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="regarewg")
        await ctx.send(embed=embed)

    
def setup(bot):
    bot.add_cog(Utility(bot))