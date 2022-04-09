import discord
from discord.ext import commands, menus
import lavalink
import re
from discord.ext.commands.errors import CheckFailure
from utils import SecondPageSource, MenuPages
import datetime
import urllib
import aiohttp


class LyricPageSource(menus.ListPageSource):
    def __init__(self, title, url, thumbnail, data):
        self.title = title
        self.url = url
        self.thumbnail = thumbnail
        super().__init__(data, per_page=20)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, url=self.url)
        embed.description = "\n".join([part for part in entries])
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class NotConnectedToVoice(CheckFailure):
    """User not connected to any voice channel"""

    pass


class BotNotConnected(CheckFailure):
    """Bot not connected"""

    pass


class MustBeSameChannel(CheckFailure):
    """Bot and user not in same channel"""

    pass


class NoPerm(CheckFailure):
    """No voice permission"""

    pass


url_rx = re.compile(r'https?://(?:www\.)?.+')


class LavalinkVoiceClient(discord.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                    'losingtime.dpaste.org',
                    2124,
                    'SleepingOnTrains',
                    'singapore',
                    'MAIN')
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_SERVER_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_STATE_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the
        # disconnect
        player.channel_id = None
        self.cleanup()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(875589545532485682)  # bot id
            bot.lavalink.add_node(
                    'losingtime.dpaste.org',
                    2124,
                    'SleepingOnTrains',
                    'singapore',
                    'MAIN')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual vc.

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a vc" etc. You can modify the above
            # if you want to do things differently.

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.author.voice.channel.rtc_region))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.
        # Since Guild.region is deprecated in dpy v2, we need to use the VoiceChannel.rtc_region instead.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a vc (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a vc so don't need listing here.
        should_connect = ctx.command.name in ('play', 'join')

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the vc.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise NotConnectedToVoice('Join a vc first.')

        if not player.is_connected:
            if not should_connect:
                raise BotNotConnected('I\'m not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise NoPerm('I need the **CONNECT** and **SPEAK** permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise MustBeSameChannel('You need to be in my vc.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.TrackStartEvent):
            schannel = self.bot.get_channel(event.player.fetch('channel'))
            embed = discord.Embed(title="Now playing", description=f"[{event.track.title}]({event.track.uri})", color=discord.Color.random())
            embed.add_field(name="Artist", value=event.track.author)
            embed.add_field(name="Duration", value=str(datetime.datetime.fromtimestamp(event.track.duration/1000.0)))
            embed.set_thumbnail(url=f"https://img.youtube.com/vi/{event.track.identifier}/hqdefault.jpg")
            await schannel.send(embed=embed)

        elif isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the vc.
            guild = self.bot.get_guild(int(event.player.guild_id))
            await guild.voice_client.disconnect(force=True)

    @commands.command(help="Join a vc to play some music", aliases=['connect'])
    async def join(self, ctx):
        await ctx.send(f"Successfully joined {ctx.author.voice.channel.mention} and received input from {ctx.channel.mention}")

    @commands.command(help="Searches and plays a song from a given query.")
    async def play(self, ctx, *, query: str):
        await ctx.trigger_typing()
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        embed = discord.Embed(color=discord.Color.random())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)

            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
        else:
            track = results['tracks'][0]
            embed.title = 'Track Enqueued'
            embed.description = f'{track["info"]["title"]}'

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    @commands.command(aliases=['disconnect'], help="Disconnects the player from the voice channel and clears its queue.")
    async def leave(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send('You\'re not in my vc!')

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)

    @commands.command(help="Pause player")
    async def pause(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            await ctx.send("I'm not playing anything")
        else:
            await player.set_pause(True)

    @commands.command(help="Resume player")
    async def resume(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await player.set_pause(False)

    @commands.command(help="Skip the current track")
    async def skip(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await player.skip()

    @commands.command(help="Shows the currently playing track.")
    async def np(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.current:
            return await ctx.send("Nothing is playing.")
        embed = discord.Embed(title="Now playing", description=f"[{player.current.title}]({player.current.uri})",
                              color=discord.Color.random())
        embed.add_field(name="Artist", value=player.current.author)
        embed.add_field(name="Duration", value=str(datetime.datetime.fromtimestamp(player.current.duration / 1000.0)))
        embed.add_field(name="Volume", value=f'{player.volume * 2}%')

        embed.set_thumbnail(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
        await ctx.send(embed=embed)

    @commands.command(aliases=['lyrc', 'lyric'], help="Shows the lyrics of a song")
    async def lyrics(self, ctx, *, song):
        await ctx.trigger_typing()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://some-random-api.ml/lyrics?title={urllib.parse.quote(song)}") as resp:
                data = await resp.json()

        if data.get('error'):
            return await ctx.send(f"Received unexpected error: {data['error']}")
        pagData = []
        for chunk in data['lyrics'].split('\n'):
            pagData.append(chunk)
        page = MenuPages(LyricPageSource(data['title'], data['links']['genius'], data['thumbnail']['genius'], pagData))
        await page.start(ctx)

    @commands.command(aliases=['vol'], help="Change bot volume")
    async def volume(self, ctx, volume: int = None):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if volume is None:
            await ctx.send(f'Volume: {player.volume * 2}%')
        else:
            volume = max(1, min(volume, 100))

            await player.set_volume(volume / 2)

    @commands.command(help="Loop the current song until the command is invoked again. ")
    async def loop(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('Nothing playing.')
        player.repeat = not player.repeat
        await ctx.send('Loop ' + ('enabled' if player.repeat else 'disabled'))

    @commands.command(help="Shows the player's queue")
    async def queue(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        playerQueueWithCurrent = [player.current] + player.queue
        if not playerQueueWithCurrent:
            return await ctx.send('Nothing queued!')
        else:
            data = []
            num = 0
            for track in playerQueueWithCurrent:
                num += 1
                to_append = (f"**{num}**", f"[**{track.title}**]({track.uri})")
                data.append(to_append)

            page = MenuPages(SecondPageSource(f"📀 Queue of {ctx.author.guild.name} 📀", data))
            await page.start(ctx)