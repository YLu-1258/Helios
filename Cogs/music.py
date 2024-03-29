import discord
import requests
import lxml.etree
import json
import re
import random
import asyncio
import pafy
from urllib.parse import quote 
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from urllib import request
from pathlib import Path

from Utility import link_tools
from Utility.link_tools import getSongs, validUrl, sortLink
from Utility.spotify import SpotifyToYoutube

#from Utility import genius
#from Utility.genius import Genius_Client


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}

# Define command errors
class InvalidArgument(commands.CommandError):
    pass

class EndOfQueue(commands.CommandError):
    pass

class IndexOutOfBounds(commands.CommandError):
    pass


class Queue:
    def __init__(self):
        self._queue = [] # _ in front of variable is to represent a private var
        self.pos = 0 # Current position in track, return to Player object to get hte track ideal for playing
        self.repmode = 0 # what repeating mode we want, 0 - no repeating, 1- loop song, 2-loop whole queue

    def add_song(self, arg):
        '''
        Add a song to the queue\n
        '''
        self._queue.append(arg)


    def set_loop(self, mode):
        '''
        Set Queue loop mode\n
        '''
        if mode == 0:
            self.repmode = 0
        elif mode == 1:
            self.repmode = 1
        elif mode == 2:
            self.repmode = 2
        else:
            raise InvalidArgument
    
    def curr_song(self):
        '''
        Get the index of the current song in Queue\n
        '''
        if self._queue:
            return self.pos
        raise EndOfQueue

    def next_song(self):
        '''
        Get the index of the next song in Queue\n
        3 Cases/Repeating modes:\n
            - MODE 0 (NO LOOP)  :  increment position by 1, return IndexOutOfBounds\n
                                   error if at the end of the song, use try/except\n
                                   to send message to client and terminate voice\n
            - MODE 1 (LOOP SONG):  do nothing, maintain the current position in \n
                                   queue\n
            - MODE 2 (LOOP QUEUE): Loop entire queue, increment by 1 if not at\n
                                   end of queue, wrap back to idx 0 when last \n
                                   song finishes playing\n
        '''
        if len(self._queue) == 0:
            raise EndOfQueue
        if self.repmode == 0:
            if self.pos < (len(self._queue)-1):
                self.pos += 1
                print("REPMODE 0: ADDED TO POS")
            else:
                raise EndOfQueue
        elif self.repmode == 1:
            pass
        elif self.repmode == 2:
            if self.pos < (len(self._queue)-1):
                self.pos += 1
                print("REPMODE 2: ADDED TO POS")
            else:
                self.pos = 0 #loop back to first song
                print("REPMODE 2: LOOPBACK")


    def clear(self):
        '''
        Clear Queue
        '''
        self._queue.clear()
        self.pos = 0
        self.repmode=0        

class Player(commands.Cog):
    def __init__(self, ctx):
        self.bot = ctx.bot
        self.ctx = ctx
        self._guild = ctx.guild
        self.Queue = Queue()
        self.next = asyncio.Event()
        self.play_songs
        self.not_playing = True
        self.current = None
        self._cog = ctx.cog

    def __del__(self):
        print("Player has been shut down")
        
    async def store_song(self, ctx, inp_song, playlist = False):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and \
            msg.content in ("p1","p2","p3","cancel", "Cancel", "c", "C")
            
        if not validUrl(inp_song):
            inp_song = inp_song.replace(" ", "+")
            raw = request.urlopen("https://www.youtube.com/results?search_query=" + quote(inp_song))
            video_ids = re.findall(r"watch\?v=(\S{11})", raw.read().decode()) # getting youtube video id with custom ReGEX
            track_list = ""
            i=0
            counter=0
            tracker = {}
            while i<3:
                try:
                    song = pafy.new(video_ids[counter])
                    track_list += "p" + str(i+1)+ ") **{0}** by *{1}*".format(song.title, song.author) +  "\n"
                    tracker[i] = counter
                    counter+=1
                    i+=1
                except:
                    counter+=1
                    continue
                if(i<3 and counter==10):
                    embed1 = discord.Embed(title="Uh Oh!", description="Could not load requested song", color=0xff0066)
                    embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
                    await ctx.send(embed=embed1, mention_author=False)
                    return
            embed1 = discord.Embed(title="Please Select a Song", description=track_list, color=0x00ffff)
            embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            embed1.set_footer(text="Pick an option or type 'cancel'")
            await ctx.send(embed=embed1, mention_author=False)
            msg = await self.bot.wait_for("message", check=check)
            if msg.content in ("cancel", "Cancel", "c", "C"):
                embed1 = discord.Embed(title="Song Selection Cancelled", description="Please try again", color=0xff0066)
                embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
                await ctx.send(embed=embed1, mention_author=False)
                return
            song_id = tracker[int(msg.content[-1])-1]
            song = pafy.new(video_ids[song_id])
        else:
            song = 'filler'
            if playlist:
                try:
                    song = pafy.new(inp_song)
                except:
                    return
            else:
                try:
                    song = pafy.new(inp_song)
                except:
                    embed1 = discord.Embed(title="Uh Oh!", description="Could not load requested song", color=0xff0066)
                    embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
                    await ctx.send(embed=embed1, mention_author=False)
                    return
        
        self.Queue.add_song(song)
        if not playlist:
            embed2 = discord.Embed(title="Successfully Queued", description="Song **{0}** by *{1}*".format(song.title, song.author), color=0x00ffff)
            embed2.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed2, mention_author=False)
        

    async def play_songs(self):
        # Wait until song finishes to run self.Queue.next_song()
        await self.bot.wait_until_ready()
        self.not_playing = False
        while self.Queue._queue:
            self.next.clear()
            try:
                self._song = self.curr_song()
                audio = self._song.getbestaudio()  # get audio source
                source = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)  # converts the youtube audio source into a source discord can use
                # Play music
                self.current = source
                embed2 = discord.Embed(title="Now Playing", description="**{0}** by *{1}*\nDuration: {2}".format(self._song.title, self._song.author, self._song.duration), color=0x00ffff, url="https://www.youtube.com/watch?v={0}".format(self._song.videoid))
                embed2.set_thumbnail(url=self._song.thumb)
                self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                if self.Queue.repmode != 1:
                    await self.ctx.send(embed=embed2)
                await self.next.wait()
                self.current = None
                self.Queue.next_song()
            except EndOfQueue:
                embed3 = discord.Embed(title="Queue has Ended", description="I have left the channel", color=0xffff00)
                await self.ctx.send(embed=embed3, mention_author=False)
                return self.destroy(self._guild)

    def curr_song(self):
        return self.Queue._queue[self.Queue.pos] 

    async def print_queue(self, page):
        tracklist = [""]
        i = 0
        counter = 0
        for song in range(0,len(self.Queue._queue)):
            if counter <= 9:
                tracklist[i] = tracklist[i] + str(song+1) + ") **{0}** by *{1}*".format(self.Queue._queue[song].title, self.Queue._queue[song].author) + "\n"
                counter += 1
            else:
                counter = 1
                i+=1
                tracklist.append("")
                tracklist[i] = tracklist[i] + str(song+1) + ") **{0}** by *{1}*".format(self.Queue._queue[song].title, self.Queue._queue[song].author) + "\n"
        content = tracklist[page-1]
        total_page=0
        if len(self.Queue._queue) % 10 != 0:
                total_page = len(self.Queue._queue) // 10 +1
        else:
            total_page= len(self.Queue._queue) // 10
        embed = discord.Embed(title="Song Playlist", description=content, color=0xfd00f5)
        embed.set_footer(text="Displaying page {0} of {1}".format(str(page),total_page))
        await self.ctx.send(embed=embed, mention_author=False)

    async def currently_playing(self):
        embed = discord.Embed(title="Currently Playing", description="**{0}** by *{1}*".format(self._song.title, self._song.author), url="https://www.youtube.com/watch?v={0}".format(self._song.videoid), color=0xfd00f5)
        embed.set_footer(text="Current position in queue is {}".format(str(self.Queue.pos+1)))
        embed.set_thumbnail(url=self._song.thumb)
        await self.ctx.send(embed=embed, mention_author=False)
        

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))

class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        self.S2Y = SpotifyToYoutube()
        #self.gclient = Genius_Client()

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx): # Function I found pretty useful
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = Player(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice = get(self.bot.voice_clients, guild=member.guild)
        if member.bot: # if bot called func or bot is not in vc or person mutes/deafeans ignore
            if before.channel and after.channel is None:
                try:
                    await voice.stop()
                    await voice.disconnect()
                except:
                    pass
                print("force disconnect ")
                print(member.guild.id)
                await self.cleanup(member.guild)
                return
            else:
                return

        if voice==None:
            return

        if before.channel == after.channel:
            return 

        elif before.channel and after.channel and before.channel == voice.channel: #player joined a different channel
            if not [m for m in voice.channel.members if not m.bot]:
                await asyncio.sleep(10)
                
                if not [m for m in voice.channel.members if not m.bot]:
                    await voice.disconnect()
                    await self.cleanup(member.guild)

        elif before.channel and after.channel is None and before.channel == voice.channel: #if player leaves a channel
            if not [m for m in voice.channel.members if not m.bot]:
                await asyncio.sleep(10)

                if not [m for m in voice.channel.members if not m.bot]:
                    await voice.disconnect()
                    await self.cleanup(member.guild)

    @commands.command(pass_context=True, brief="Joins the channel", aliases=['j'])
    async def join(self, ctx):
        channel = ctx.message.author.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channel = ctx.message.author.voice.channel
        voice = get(ctx.guild.voice_channels, name=channel.name)
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client == None:
            voice_client = await voice.connect()
        else:
            await voice_client.move_to(channel)
        await ctx.guild.change_voice_state(channel=channel, self_mute=True, self_deaf=True)
        embed = discord.Embed(title=f"Joined {channel}", color=0xfd00f5)
        embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, brief="plays a song!", aliases=['p','paly'])
    async def play(self, ctx, *, search=''):
        """Plays a song"""
        channel = ctx.message.author.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if search == '':
            embed = discord.Embed(title="Uh Oh!", description="Please provide something to play", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        
        # Get information about voice call 
        channel = ctx.message.author.voice.channel
        voice = get(ctx.guild.voice_channels, name=channel.name)
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        

        # Check if our bot is currently in a voice call, if not, connect to call, if yes, move to call
        if voice_client == None:
                voice_client = await voice.connect()
        else:
                await voice_client.move_to(channel)
        await ctx.guild.change_voice_state(channel=channel, self_mute=True, self_deaf=True)

        inpt_type = sortLink(search)

        # Youtube song
        if inpt_type == link_tools.LinkType.YOUTUBE:
            await player.store_song(ctx, search, False)

        # Youtube Playlist
        elif inpt_type == link_tools.LinkType.YOUTUBE_PLAYLIST:
            ids = getSongs(search)
            for videoId in ids:
                await player.store_song(ctx, videoId, True)
            embed2 = discord.Embed(title="Requested Youtube Playlist has Been Queued", color=0x00ffff)
            embed2.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed2, mention_author=False)

        # Spotify Song
        elif inpt_type == link_tools.LinkType.SPOTIFY:
            query = self.S2Y.link_to_yt(search)
            await player.store_song(ctx, query, False)

        # Spotify Playlist
        elif inpt_type == link_tools.LinkType.SPOTIFY_PLAYLIST:
            pl = self.S2Y.playlist_to_yt(search)
            for query in pl:
                await player.store_song(ctx, query, True)
            embed2 = discord.Embed(title="Requested Spotify Playlist has Been Queued", color=0x00ffff)
            embed2.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed2, mention_author=False)
        
        # Search By Name
        elif inpt_type == link_tools.LinkType.UNKNOWN:
            await player.store_song(ctx, search, False)
        

        if player.not_playing and player.Queue._queue:
            await player.play_songs()
        
    
    @commands.command(pass_context=True, brief="Makes the bot leave your channel", aliases=['l'])
    async def leave(self, ctx):
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.disconnect()
            embed = discord.Embed(title=f"Left {channel}", color=0xfd00f5)
            embed.set_footer(text="Called by {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)


    @commands.command(pass_context=True, brief='Pauses the currently playing music', aliases=['pa', 'stop'])
    async def pause(self, ctx):
        """Pause the currently playing song."""
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_playing():
            embed = discord.Embed(title="Uh Oh!", description="I am currently not playing anything", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.message.add_reaction("⏸️")


    @commands.command(pass_context = True, brief='Resumes the currently paused track', aliases=['re','start'])
    async def resume(self, ctx):
        """Resume the currently paused song."""
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        if not vc or vc.is_playing():
            embed = discord.Embed(title="Uh Oh!", description="I am already playing something", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            embed = discord.Embed(title="Uh Oh!", description="I am currently not playing anything", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)

        vc.resume()
        await ctx.message.add_reaction("⏯️")

    @commands.command(pass_context = True, brief='Stops the current track', aliases=["sk","next"])
    async def skip(self, ctx, pos=None):
        """Stops\Skips the currently playing song."""
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)

        if pos is None:
            vc.stop()
            await ctx.message.add_reaction("⏹️")
            return
        try:
            pos = int(pos) - 1
            if pos in range(0,len(player.Queue._queue)):
                player.Queue.pos = pos-1
                if player.Queue.repmode ==1:
                    player.Queue.repmode = 0
                vc.stop()
                await ctx.message.add_reaction("⏹️")
            else:
                embed = discord.Embed(title="Uh Oh!", description="Invalid input", color=0xff0066)
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
                await ctx.send(embed=embed)
        except:
            embed = discord.Embed(title="Uh Oh!", description="Invalid input", color=0xff0066)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)            

    @commands.command(pass_context = True, brief='Displays the current Playlist/Queue', aliases=['playlist', 'q'])
    async def queue(self, ctx, *, page=1):
        """Stops the currently playing song."""
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        player = self.get_player(ctx)
        page = int(page)
        try:
            await player.print_queue(page)
        except:
            embed = discord.Embed(title="Uh Oh!", description="Invalid input", color=0xff0066)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

    @commands.command(pass_context = True, brief='loops a way based on input', aliases=['lop'])
    async def loop(self, ctx, pos='current'):
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        if pos in ('0', 'un' , 'u'):
            player.Queue.repmode = 0
            embed = discord.Embed(title="Unlooping Song/Track!", color=0xfd00f5)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed, mention_author=False)
        elif pos in ('1', 'current', 'song'):
            player.Queue.repmode = 1
            embed = discord.Embed(title="Looping Song!", description="Now looping: **{0}** by *{1}*".format(player.Queue._queue[player.Queue.pos].title, player.Queue._queue[player.Queue.pos].author), color=0xfd00f5, url="https://www.youtube.com/watch?v={0}".format(player.Queue._queue[player.Queue.pos].videoid))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            embed.set_thumbnail(url=player.Queue._queue[player.Queue.pos].thumb)
            embed.set_footer(text="Duration: {0}".format(str(player.Queue._queue[player.Queue.pos].duration)))
            await ctx.send(embed=embed, mention_author=False)
        elif pos in ('2', 'all', 'track'):
            player.Queue.repmode = 2
            embed = discord.Embed(title="Looping Track!", color=0xfd00f5)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(title="Uh Oh!", description="Invalid input", color=0xff0066)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

    @commands.command(pass_context = True, brief='shuffles track', aliases=['sh'])
    async def shuffle(self, ctx):
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        random.shuffle(player.Queue._queue)
        
        embed = discord.Embed(title="Shuffling Track!", color=0xfd00f5)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed, mention_author=False)
        player.Queue.pos-=1
        if player.Queue.repmode ==1:
            player.Queue.repmode = 0
        vc = ctx.voice_client
        vc.stop()
    
    @commands.command(pass_context = True, brief='Removes the song at the index', aliases=['rm', "delete"])
    async def remove(self, ctx, pos='current'):
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        if pos == 'current':
            pos=player.Queue.pos
            embed = discord.Embed(title="Removing Song", description="**{0}** by *{1}*".format(player.Queue._queue[pos].title, player.Queue._queue[pos].author), color=0xfd00f5)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            player.Queue._queue.pop(pos)
            if player.Queue.repmode==1 and pos == player.Queue.pos:
                player.Queue.repmode=0
            if pos == player.Queue.pos:
                player.Queue.pos-=1
                vc.stop()
            await ctx.send(embed=embed, mention_author=False)
            return
        if pos in ("a","all"):
            player.Queue.clear()
            vc.stop()
            return
        try:
            pos = int(pos) - 1
            embed = discord.Embed(title="Removing Song", description="**{0}** by *{1}*".format(player.Queue._queue[pos].title, player.Queue._queue[pos].author), color=0xfd00f5)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            player.Queue._queue.pop(pos)
            if player.Queue.repmode==1 and pos == player.Queue.pos:
                player.Queue.repmode=0
            if pos == player.Queue.pos:
                player.Queue.pos-=1
                vc.stop()
            elif pos < player.Queue.pos:
                player.Queue.pos-=1
            await ctx.send(embed=embed, mention_author=False)
        except:
            embed = discord.Embed(title="Uh Oh!", description="Invalid input", color=0xff0066)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

    @commands.command(pass_context = True, brief='Shows currently playing song', aliases=['info', "cur"])
    async def current_song(self, ctx):
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        if player.Queue._queue:
            await player.currently_playing()
        else:
            embed = discord.Embed(title="Uh Oh!", description="I am currently not playing anything", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)

    @commands.command(pass_context = True, brief='restarts a song', aliases=['rep'])
    async def restart(self, ctx, pos=''):
        channel = ctx.message.author.voice
        channelid = ctx.message.author.voice
        bot_channel = ctx.guild.me.voice
        if channel == None:
            embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        if not bot_channel:
            embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        channelid = ctx.message.author.voice.channel.id
        bot_channel = ctx.guild.me.voice.channel.id
        channel = ctx.message.author.voice.channel
        if bot_channel != channelid:
            embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return await ctx.send(embed=embed)
        vc = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        if pos in ("all", "a", "track"):
            embed = discord.Embed(title="Restarting Track", color=0xfd00f5)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed, mention_author=False)
            player.Queue.pos = -1
            if player.Queue.repmode==1:
                player.Queue.repmode=0
            vc.stop()
        elif pos == '':
            embed = discord.Embed(title="Restarting Song", color=0xfd00f5)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed, mention_author=False)
            player.Queue.pos-=1
            vc.stop()
        else:
            embed = discord.Embed(title="Uh Oh!", description="Invalid input", color=0xff4d94)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

#    @commands.command(pass_context = True, brief='Shows the lyrics of the song', aliases=['lyric', 'lyr'])
#    async def lyrics(self, ctx, *, search=''):
#        player = self.get_player(ctx)
#        if search == '':
#            channel = ctx.message.author.voice
#            channelid = ctx.message.author.voice
#            bot_channel = ctx.guild.me.voice
#            if channel == None:
#                embed = discord.Embed(title="Uh Oh!", description="Join a voice channel before using this command", color=0xff9900)
#                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
#                return await ctx.send(embed=embed)
#            if not bot_channel:
#                embed = discord.Embed(title="Uh Oh!", description="I need to join a channel before using this command", color=0xff9900)
#                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
#                return await ctx.send(embed=embed)
#            channelid = ctx.message.author.voice.channel.id
#            bot_channel = ctx.guild.me.voice.channel.id
#            channel = ctx.message.author.voice.channel
#            if bot_channel != channelid:
#                embed = discord.Embed(title="Uh Oh!", description="Join my channel before using this command", color=0xff9900)
#                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
#                return await ctx.send(embed=embed)
#            vc = get(self.bot.voice_clients, guild=ctx.guild)
#            player = self.get_player(ctx)
#            CURR_SONG = player.Queue._queue[player.Queue.pos].title
#        else:
#            CURR_SONG = search
#
#        song = self.gclient.get_lyric(CURR_SONG)
#        if song is None:
#            embed = discord.Embed(title="Uh Oh!", description="Could not find the lyrics to the song", color=0xff0000)
#            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
#            await ctx.send(embed=embed)
#            return
#        song_front_buffer = len(song.title + " lyrics")
#        song_back_buffer = len(song.lyrics)-5
#        embed = discord.Embed(title="Lyrics of {} by {}".format(song.title, song.artist), description = song.lyrics[song_front_buffer:song_back_buffer], color=0xfd00f5)
#        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
#        await ctx.send(embed=embed, mention_author=False)

    
async def setup(bot):
    await bot.add_cog(Music(bot))