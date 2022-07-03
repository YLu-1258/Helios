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

    @commands.command(aliases=["clearchat", "clear", "spoilers"])
    async def clearcht(ctx, amount=10):
        print("Clear request sent from user {0} of number {1}".format(str(ctx.message.author), amount))
        amount += 1
        if amount > 1:
            await ctx.channel.purge(limit=amount)
            embed = discord.Embed(title="Clearing Chat", description=f"Purged {amount - 1} texts", color=0xff8b00)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)
        else:
            await ctx.channel.purge(limit=1)
            embed = discord.Embed(title="Error", description=f"Improper number", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)

    
def setup(bot):
    bot.add_cog(Utility(bot))