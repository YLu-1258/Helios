import discord
import youtube_dl
import os
import time
import random
import asyncio
import pafy


from discord.errors import Forbidden
from urllib import request
from re import findall as fa
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from os import system

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
bot = commands.Bot(command_prefix=["."])
songs = asyncio.Queue()
play_next_song = asyncio.Event()

#BOT SETUP
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('Smurfin in diamond lobbies'))
    print("{0} has sucessfully connected to Discord".format(bot.user))

#BOT SHUTDOWN
@bot.command()
async def shutdown(ctx):
    await ctx.send("The sun has set")
    print("Shutting down...")
    await ctx.bot.logout()


#BOT JOIN VC
@bot.command(pass_context=True, brief="Makes the bot join your channel", aliases=[' join',])
async def join(ctx):
    channel = ctx.message.author.voice
    if not channel:
        await ctx.reply("You are not connected to a voice channel")
        return
    channel = channel.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    await ctx.reply(f"Joined {channel}")

#BOT LEAVE
@bot.command(pass_context=True, brief="Makes the bot leave your channel", aliases=['l'])
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    channelid = ctx.message.author.voice.channel.id
    bot_channel = ctx.guild.me.voice.channel.id
    if bot_channel != channelid:
        await ctx.reply("You are not in my channel")
        return
    elif not channel:
        await ctx.reply("You are not in a channel")
        return
    if not channel:
        await ctx.reply("I am not in a voice channel")
        return
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.reply(f"Left {channel}")
    else:
        await ctx.reply("I am not in a voice channel")

@bot.command(pass_context=True, brief="plays a song", aliases=['p'])
async def play(ctx, *, search=''):
    channel = ctx.message.author.voice
    if not channel:
        await ctx.reply("Join a voice channel before you use this command")
        return

    # Get information about voice call 
    channel = channel.channel
    voice = get(ctx.guild.voice_channels, name=channel.name)
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    # Check if our bot is currently in a voice call, if not, connect to call, if yes, move to call
    if voice_client == None:
            voice_client = await voice.connect()
    else:
            await voice_client.move_to(channel)

    search = search.replace(" ", "+") #formatting search query for youtube

    # Webscrape youtube for most relevant serach
    raw = request.urlopen("https://www.youtube.com/results?search_query=" + search)
    video_ids = fa(r"watch\?v=(\S{11})", raw.read().decode()) # getting youtube video id with custom ReGEX
    await ctx.reply("now playing: https://www.youtube.com/watch?v=" + video_ids[0])

    song = pafy.new(video_ids[0])

    audio = song.getbestaudio()  # get audio source

    source = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)  # converts the youtube audio source into a source discord can use

    voice_client.play(source)

### UTILITY
@bot.command(aliases=["ping"])
async def whatismyping(ctx):
    print("Ping request sent from user {0}".format(str(ctx.message.author)))
    await ctx.reply(f"The bot's ping is {round(bot.latency * 1000)} ms")

@bot.command(aliases=["clearchat", "clear", "spoilers"])
async def clearcht(ctx, amount=10):
    print("Clear request sent from user {0} of number {1}".format(str(ctx.message.author), amount))
    amount += 1
    if amount > 1:
        await ctx.channel.purge(limit=amount)
        await ctx.reply(f"No spoilers huh?\nDeleted {amount - 1} texts")
    else:
        await ctx.channel.purge(limit=1)
        await ctx.reply(f"Enter a proper number dumbass")    

@bot.command(aliases=["8ball", "8b"])
async def eightball(ctx, *, question):
    print("8ball request sent from user {0}".format(str(ctx.message.author)))
    answers = ["It is certain.",
                "It is decidedly so.",
                "Without a doubt.",
                "Yes - definitely.",
                "You may rely on it.",
                "As I see it, yes.",
                "Most likely.",
                "Outlook good.",
                "Yes.",
                "No.",
                "Signs point to yes.",
                "Reply hazy, try again.",
                "Ask again later.",
                "Better not tell you now.",
                "Cannot predict now.",
                "Concentrate and ask again.",
                "Don't count on it.",
                "My reply is no.",
                "My sources say no.",
                "Outlook not so good.",
                "Very doubtful.",
                "In your dreams."]
    await ctx.reply(f"Your Question: {question}\n8ball: {random.choice(answers)}")

    #help

    client = commands.Bot(command_prefix= ".")
    bot.remove_command("help")

    @client.group(invoke_without_command = True)
    async def help(ctx):
        em = discord.Embed(title = "Help", description = "do .help [cmd] for more info", color = ctx.author.color)
        em.add_field(name = "Music", value = "play, leave, pause, resume, queue, remove, skip, loopsong, loopqueue, unloop, shuffle")

        await ctx.send(embed = em)


# MODERATION
# Moderation
@bot.command()
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked.")

@bot.command()
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} is an asshead.")

@bot.command()
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.spilt("#")

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f"{user.mention} has been unbanned.")
            return

bot.run("OTY0Mzg1MDQ4MTEzNTg2MjU2.Ylj3kA.vCSQtSV6u0wRrDq8SLhW6mtfsrg")