import discord
from discord.ext import commands

class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True, brief = 'Kicks a user', aliases = ['k'])
    @commands.has_permissions(manage_roles=True, kick_members=True)
    async def kick(self, ctx, member : discord.Member, *, reason=None):
        try:
            user_dm = await member.create_dm()
            embed = embed = discord.Embed(title="Uh Oh!", description="You have been kicked from **{0}**".format(ctx.guild.name), color=0xff0000) 
            embed.set_footer(text="Reason: {0}".format(reason))
            await user_dm.send(embed=embed)
            await member.kick(reason=reason)
            embed = discord.Embed(title="Member Kicked", description=f"{member.mention} has been kicked for {reason}", color=0x00ff00)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(title="Member not in server", description=f"Please try again with a real member", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(pass_context = True, brief = 'Bans a User', aliases = ['b'])
    @commands.has_permissions(manage_roles=True, ban_members=True)
    async def ban(self, ctx, member : discord.Member, *, reason=None):
        try:
            user_dm = await member.create_dm()
            embed = embed = discord.Embed(title="Uh Oh!", description="You have been banned from **{0}**".format(ctx.guild.name), color=0xff0000) 
            embed.set_footer(text="Reason: {0}".format(reason))
            await user_dm.send(embed=embed)
            await member.ban(reason=reason)
            embed = discord.Embed(title="Member Banned", description=f"{member.mention} has been banned for {reason}", color=0xff00)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(title="Member not in server", description=f"Please try again with a real member", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(pass_context = True, brief = 'Unbans a user', aliases = ['ub'])
    @commands.has_permissions(manage_roles=True, ban_members=True)
    async def unban(self, ctx, member, *, reason=None):
        try:
            member = await self.bot.fetch_user(member)
            await ctx.guild.unban(member)
            embed = discord.Embed(title="Member Unbanned", description=f"GG! {member.mention} has been unbanned for {reason}", color=0x00ff00)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)
            user_dm = await member.create_dm()
            embed = embed = discord.Embed(title="GG!", description="You have been unbanned from {0}".format(ctx.guild.name), color=0x00ff00) 
            embed.set_footer(text="Reason: {0}".format(reason))
            await user_dm.send(embed=embed)
        except discord.NotFound:
            embed = discord.Embed(title="Member not banned", description=f"Please try again with a banned member", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Moderation(bot))