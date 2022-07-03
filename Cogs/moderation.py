import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @has_permissions(manage_roles=True, kick_members=True)
    async def kick(ctx, member : discord.Member, *, reason=None):
        await member.kick(reason=reason)
        embed = discord.Embed(title="Member Kicked", description=f"{member.mention} has been kicked for {reason}", color=0xff0000)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(manage_roles=True, ban_members=True)
    async def ban(ctx, member : discord.Member, *, reason=None):
        await member.ban(reason=reason)
        embed = discord.Embed(title="Member Banned", description=f"{member.mention} has been banned for {reason}", color=0xff0000)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(manage_roles=True, ban_members=True)
    async def unban(ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.spilt("#")

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                embed = discord.Embed(title="Member Unbanned", description=f"{member.mention} has been unbanned", color=0x00ff00)
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
                await ctx.send(embed=embed)
                return

def setup(bot):
    bot.add_cog(Moderation(bot))