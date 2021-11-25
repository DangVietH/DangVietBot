import math
import re
from discord.ext.commands.errors import CheckFailure
import discord
import lavalink
from discord.ext import commands

url_rx = re.compile(r'https?://(?:www\.)?.+')


class NotConnectedToVoice(CheckFailure):
    pass


class BotNotConnected(CheckFailure):
    pass


class MustBeSameChannel(CheckFailure):
    pass


class MissingPermissions(CheckFailure):
    pass


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.music = lavalink.Client(875589545532485682)
            bot.music.add_node('lava.link', 80, 'anything', 'singapore', 'MAIN')
            bot.add_listener(bot.music.voice_update_handler, 'on_socket_response')

        bot.music.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.music._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        await self.ensure_voice(ctx)

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise NotConnectedToVoice('Join a vc first.')

        if not player.is_connected:
            if not should_connect:
                raise NotConnectedToVoice('Not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise MissingPermissions('I need the **CONNECT** and **SPEAK** permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
            await player.set_volume(50)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise NotConnectedToVoice('You need to be in my vc.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.TrackStartEvent):
            c = event.player.fetch('channel')
            if c:
                sc = self.bot.get_channel(c)
                if sc:
                    embed = discord.Embed(colour=c.guild.me.top_role.colour, title='Now Playing',
                                          description=f"[{event.track.title}]({event.track.uri})")
                    embed.set_thumbnail(url=event.track.thumbnail)
                    await sc.send(embed=embed)
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a track from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.music.player_manager.get(ctx.guild.id)
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
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    @commands.command()
    async def np(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        if not player.current:
            return await ctx.send("Nothing is playing.")

        position = lavalink.utils.format_time(player.position)
        if player.current.stream:
            duration = '🔴 LIVE'
        else:
            duration = lavalink.utils.format_time(player.current.duration)
        track = f'**[{player.current.title}]({player.current.uri})**\n**Duration:** ({position}/{duration})'

        embed = discord.Embed(color=discord.Color.random(), title="Now Playing", description=track)
        await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx, page: int = 1):
        """ Shows the player's queue. """
        player = self.bot.music.player_manager.get(ctx.guild.id)
        playerQueueWithCurrent = [player.current] + player.queue

        if not playerQueueWithCurrent:
            return await ctx.send('Nothing queued.')

        items_per_page = 10
        pages = math.ceil(len(playerQueueWithCurrent) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(playerQueueWithCurrent[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=discord.Color.random(),
                              description=f'**{len(playerQueueWithCurrent)} tracks**\n\n{queue_list}')
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(aliases=['vol'])
    async def volume(self, ctx, volume: int = None):
        """Changes the bot volume (1-100)."""
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not volume:
            return await ctx.send(f'🔈 | {player.volume * 2}%')
        volume = max(1, min(volume, 100))

        await player.set_volume(volume / 2)

    @commands.command()
    async def shuffle(self, ctx):
        """ Shuffles the player's queue. """
        player = self.bot.music.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('Nothing playing.')

        player.shuffle = not player.shuffle
        await ctx.send('🔀 | Shuffle ' + ('enabled' if player.shuffle else 'disabled'))

    @commands.command()
    async def loop(self, ctx):
        """ Repeats the current song until the command is invoked again. """
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('Nothing playing.')

        player.repeat = not player.repeat
        await ctx.send('🔁 | Repeat ' + ('enabled' if player.repeat else 'disabled'))

    @commands.command()
    async def seek(self, ctx, *, seconds: int):
        """ Seeks to a given position in a track. """
        player = self.bot.music.player_manager.get(ctx.guild.id)

        track_time = player.position + (seconds * 1000)
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.utils.format_time(track_time)}**')

    @commands.command()
    async def pause(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        await player.set_pause(True)

    @commands.command()
    async def resume(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        await player.set_pause(False)

    @commands.command()
    async def leave(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            raise NotConnectedToVoice('You need to be in my vc.')
        player.queue.clear()
        await player.stop()
        await ctx.guild.change_voice_state(channel=None)


def setup(bot):
    bot.add_cog(Music(bot))