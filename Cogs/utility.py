import discord
from discord.ext import commands

class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True, brief = 'All commands for bot', aliases = ['h'])
    async def help(self,ctx):
        embed = discord.Embed(
            title = 'Help',
            description = 'List of All Commands'
        )
        
        embed.set_footer(text=f'Requested by - {ctx.author}', icon_url=ctx.author.avatar_url)
        embed.add_field(name = 'Music CMDS', value = '`play`, `leave`, `pause`, `resume`, `queue`, `remove`, `skip`, `loopsong`, `loopqueue`, `unloop`, `shuffle`, `current`')
        await ctx.send(embed = embed)

    
def setup(bot):
    bot.add_cog(Utility(bot))