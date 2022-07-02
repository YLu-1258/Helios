import discord
from urllib import request
import re
import random
import asyncio
import pafy
from async_timeout import timeout
from functools import partial
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}

# Define command errors
class InvalidArgument(commands.CommandError):
    pass

class ShortQueue(commands.CommandError):
    pass

class IndexOutOfBounds(commands.CommandError):
    pass



def valid_url(query):
    url_re = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return re.match(url_re, query) is not None

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
        raise ShortQueue

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
        if self.repmode == 0:
            if self.pos < (len(self._queue)-1):
                self.pos += 1
                print("REPMODE 0: ADDED TO POS")
            else:
                raise ShortQueue
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
        
    async def store_song(self, ctx, inp_song):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and \
            msg.content in ("1","2","3","cancel", "Cancel", "c", "C")
            
        if not valid_url(inp_song):
            inp_song = inp_song.replace(" ", "+")
            raw = request.urlopen("https://www.youtube.com/results?search_query=" + inp_song)
            video_ids = re.findall(r"watch\?v=(\S{11})", raw.read().decode()) # getting youtube video id with custom ReGEX
            track_list = ""
            for i in range(0,3):
                song = pafy.new(video_ids[i])
                track_list = track_list + str(i+1)+ ") **{0}** by *{1}*".format(song.title, song.author) +  "\n"
            embed1 = discord.Embed(title="Please select a song", description=track_list, color=0x00ffff)
            embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed1.set_footer(text="Pick an Index 1-3.")
            await ctx.reply(embed=embed1, mention_author=False)
            msg = await self.bot.wait_for("message", check=check)
            if msg.content in ("cancel", "Cancel", "c", "C"):
                embed1 = discord.Embed(title="Cancelling song selection", description="Please try again", color=0xff0000)
                embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                embed1.set_footer(text="Called by {0}".format(ctx.author.display_name))
                await ctx.reply(embed=embed1, mention_author=False)
                return
            song_id = int(msg.content)-1
            song = pafy.new(video_ids[song_id])
        else:
            song = pafy.new(inp_song)
        
        self.Queue.add_song(song)
        embed2 = discord.Embed(title="Song", description="Song **{0}** by *{1}* has been successfully queued!".format(song.title, song.author), color=0x00ffff)
        embed2.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed2.set_footer(text="Called by: {0}".format(ctx.author.display_name))
        await ctx.reply(embed=embed2, mention_author=False)
        

    async def play_songs(self):
        # Wait until song finishes to run self.Queue.next_song()
        await self.bot.wait_until_ready()
        self.not_playing = False
        while self.Queue._queue:
            self.next.clear()
            try:
                song = self.curr_song()
                audio = song.getbestaudio()  # get audio source
                source = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)  # converts the youtube audio source into a source discord can use
                # Play music
                self.current = source
                embed2 = discord.Embed(title="Playing Song!", description="Now playing: **{0}** by *{1}*".format(song.title, song.author), color=0x00ffff, url="https://www.youtube.com/watch?v={0}".format(song.videoid))
                embed2.set_author(name=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url)
                embed2.set_thumbnail(url=song.thumb)
                embed2.set_footer(text="Duration: {0}".format(str(song.duration)))
                self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                await self.ctx.send(embed=embed2)
                await self.next.wait()
                self.current = None
                self.Queue.next_song()
            except ShortQueue:
                embed3 = discord.Embed(title="Uh oh! ", description="The Queue has Ended, Player will now terminate, POS: {0}, Total {1}".format(self.Queue.pos, len(self.Queue._queue)), color=0xff0000)
                embed3.set_author(name=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url)
                embed3.set_footer(text="We hope you had fun!")
                await self.ctx.send(embed=embed3, mention_author=False)
                return self.destroy(self._guild)
        self.not_playing = True

    def curr_song(self):
        return self.Queue._queue[self.Queue.pos] 

    def set_loop_mode(self, mode):
        if mode not in (0,1,2):

            raise InvalidArgument
        self.Queue.repmode = mode

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
        embed = discord.Embed(title="Playlist ", description=content, color=0xfd00f5)
        embed.set_author(name=self.ctx.author.display_name, icon_url=self.ctx.author.avatar_url)
        embed.set_footer(text="Currently displaying page {}".format(str(page)))
        await self.ctx.reply(embed=embed, mention_author=False)

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        self.Queue.clear()
        return self.bot.loop.create_task(self._cog.cleanup(guild))

    async def skip_to(self, pos):
        self._guild.voice_client.stop
        self.Queue.pos = pos

    async def remove(self, pos):
        pos-=1
        self.Queue._queue.pop(pos)

class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

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

    @commands.command(pass_context=True, brief="plays a song!", aliases=['p', 'paly', 'pl'])
    async def play(self, ctx, *, search=''):
        """Plays a song"""
        channel = ctx.message.author.voice
        if not channel:
            await ctx.reply("Join a voice channel before you use this command")
            return

        # Get information about voice call 
        channel = channel.channel
        voice = get(ctx.guild.voice_channels, name=channel.name)
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        player = self.get_player(ctx)
        

        # Check if our bot is currently in a voice call, if not, connect to call, if yes, move to call
        if voice_client == None:
                voice_client = await voice.connect()
        else:
                await voice_client.move_to(channel)

        await player.store_song(ctx, search)

        if player.not_playing:
            await player.play_songs()
        
    
    @commands.command(pass_context=True, brief="Makes the bot leave your channel", aliases=['l'])
    async def leave(self, ctx):
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
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.reply(f"Left {channel}")
        else:
            await ctx.reply("I am not in a voice channel")


    @commands.command(pass_context=True, brief='Pauses the currently playing music', aliases=['pa'])
    async def pause(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title="Uh Oh!", description="I am currently not playing anything", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Please try again with a song")
            return await ctx.reply(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.message.add_reaction("⏸️")


    @commands.command(pass_context = True, brief='Resumes the currently paused track', aliases=['r', 're'])
    async def resume(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="Uh Oh!", description="I'm not connected to a voice channel or there are no currently playing songs", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Please try again with a song")
            return await ctx.reply(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.message.add_reaction("⏯️")

    @commands.command(pass_context = True, brief='Stops the current track', aliases=['st', 'stp'])
    async def stop(self, ctx):
        """Stops the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="Uh Oh!", description="I'm not connected to a voice channel or there are no currently playing songs", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Please try again with a song")
            return await ctx.reply(embed=embed)


        vc.stop()
        await ctx.message.add_reaction("⏹️")

    @commands.command(pass_context = True, brief='Skip to a track index', aliases=['sk', 'ski'])
    async def skip(self, ctx, *, idx=1):
        """Stops the currently playing song."""
        idx = int(idx)
        vc = ctx.voice_client
        player = self.get_player(ctx)
        if not vc or not vc.is_connected():
            embed = discord.Embed(title="Uh Oh!", description="I'm not connected to a voice channel or there are no currently playing songs", color=0xff0000)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text="Please try again with a song")
            return await ctx.reply(embed=embed)

        await player.skip_to(idx)
        
        await ctx.message.add_reaction("⏩")

    @commands.command(pass_context = True, brief='Displays the current Playlist/Queue', aliases=['playlist', 'q', 'plist', 'list'])
    async def queue(self, ctx, *, page=1):
        """Stops the currently playing song."""
        try:
            page = int(page)
        except:
            embed = discord.Embed(title="Error", description="Please Give me a number!", color="0xff0000")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url=player.Queue._queue[player.Queue.pos].thumb)
            await ctx.reply(embed=embed)
        player = self.get_player(ctx)
        await player.print_queue(page)

    @commands.command(pass_context = True, brief='Loops the current song', aliases=['loopsong','loopcurrent','loopcurrentsong'])
    async def loop_song(self, ctx):
        player = self.get_player(ctx)
        player.Queue.repmode = 1
        embed = discord.Embed(title="Looping Song!", description="Now looping: **{0}** by *{1}*".format(player.Queue._queue[player.Queue.pos].title, player.Queue._queue[player.Queue.pos].author), color=0x00ffff, url="https://www.youtube.com/watch?v={0}".format(player.Queue._queue[player.Queue.pos].videoid))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=player.Queue._queue[player.Queue.pos].thumb)
        embed.set_footer(text="Duration: {0}".format(str(player.Queue._queue[player.Queue.pos].duration)))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(pass_context = True, brief='Loops the entire track/queue', aliases=['looptrack','loopqueue','loopall', "lt", "lq", "la"])
    async def loop_track(self, ctx):
        player = self.get_player(ctx)
        player.Queue.repmode = 2
        embed = discord.Embed(title="Looping Track!", color=0x00ffff)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(pass_context = True, brief='unloops the track or song', aliases=['unloop','unloopsong','unlooptrack', "ul", "uls", ])
    async def un_loop(self, ctx):
        player = self.get_player(ctx)
        player.Queue.repmode = 0
        embed = discord.Embed(title="Unlooping Song/Track!", color=0x00ffff)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(pass_context = True, brief='shuffles track', aliases=['shuffletrack','shuffleall'])
    async def shuffle(self, ctx):
        player = self.get_player(ctx)
        random.shuffle(player.Queue._queue)
        embed = discord.Embed(title="Shuffling Track!", color=0x00ffff)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(pass_context = True, brief='Removes the song at the index', aliases=['rm', "del", "delete"])
    async def remove(self, ctx, pos):
        pos = int(pos) - 1
        player = self.get_player(ctx)
        try:
            embed = discord.Embed(title="Remove Song", description="Song {0} by {1} has been removed".format(player.Queue._queue[pos].title, player.Queue._queue[pos].author), color=0x00ffff)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            player.remove(pos)
            await ctx.reply(embed=embed, mention_author=False)
        except:
            embed = discord.Embed(title="Error", description="Invalid Input!", color="0xff0000")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.reply(embed=embed)

    @commands.command(pass_context = True, brief='DEBUG: Gets position and total of queue', aliases=['pos'])
    async def get_pos(self, ctx):
        player = self.get_player(ctx)
        embed = discord.Embed(title="POS: {0} TOTAL: {0}".format((player.Queue.pos - 1), player.Queue.total), color=0x00ffff)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.reply(embed=embed, mention_author=False)


    
def setup(bot):
    bot.add_cog(Music(bot))