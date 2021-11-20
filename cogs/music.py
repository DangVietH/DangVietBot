from discord.ext import commands
import lavalink
import re
import math
import discord

url_rx = re.compile(r'https?://(?:www\.)?.+')


class MusicError(commands.CommandError):
    def __init(self, message=""):
        super().__init__(message)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        bot.music = lavalink.Client(875589545532485682)
        bot.music.add_node('lava.darrennathanael.com', 443, 'airportgateway', 'us', 'default-node')
        bot.add_listener(bot.music.voice_update_handler, 'on_socket_response')
        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        self.bot.music._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        await self.ensure_voice(ctx)
        #  Ensure that the bot and command author share a mutual vc.

    async def ensure_voice(self, ctx):
        player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise MusicError('Join a vc first!')

        if not player.is_connected:
            if not should_connect:
                raise MusicError("I'm not connected to VC!")

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise MusicError('I need the **CONNECT** and **SPEAK** permissions!')

            player.store('channel', ctx.channel.id)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
            await player.set_volume(50)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise MusicError('You need to be in my vc!')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

    @commands.command(help="Play music")
    async def play(self, ctx, *, query: str):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        query = query.strip('<>')
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        embed = discord.Embed(color=discord.Color.random())
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
            vid_id = track["info"]["identifier"]
            embed.set_thumbnail(url=f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg")

            track = lavalink.models.AudioTrack(track, ctx.author.id)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=embed)
        if not player.is_playing:
            await player.play()

    @commands.command(help="see queue")
    async def queue(self, ctx, page: int = 1):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(player.queue[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=discord.Color.blurple(),
                              description=f'**{len(player.queue)} tracks**\n\n{queue_list}')
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(help="See what song I'm currently playing")
    async def np(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.current:
            return await ctx.send("Did I forgot to play something")

        position = lavalink.utils.format_time(player.position)
        if player.current.stream:
            duration = 'LIVE'
        else:
            duration = lavalink.utils.format_time(player.current.duration)
        track = f'**[{player.current.title}]({player.current.uri})**\n({position}/{duration})'

        embed = discord.Embed(color=discord.Color.random(), title="Now Playing", description=track)

        if (currentTrackData := player.fetch("currentTrackData")) is not None:
            embed.set_thumbnail(url=currentTrackData["thumbnail"]["genius"])
            embed.description += f"\n[LYRICS]({currentTrackData['links']['genius']})"

        await ctx.send(embed=embed)

    @commands.command(help="Set volume")
    async def volume(self, ctx, volume: int):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        volume = max(1, min(volume, 100))

        await player.set_volume(volume / 2)

    @commands.command(help="Pause player")
    async def pause(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("I'm not playing anything right now!")
        else:
            await player.set_pause(True)
            await ctx.message.add_reaction("🎵")

    @commands.command(help="Resume player")
    async def resume(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("I'm not playing anything right now!")
        else:
            await player.set_pause(False)
            await ctx.message.add_reaction("🎵")

    @commands.command(help="Skip song")
    async def skip(self, ctx):
        """ Skips the current track. """
        player = self.bot.music.player_manager.get(ctx.guild.id)
        await player.skip()
        await ctx.message.add_reaction("🎵")

    @commands.command(help="Skip song")
    async def resume(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        await player.skip()
        await ctx.message.add_reaction("🎵")

    @commands.command(help="Leave vc")
    async def leave(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send("You're not in my VC!")
        player.queue.clear()
        await player.stop()
        await ctx.guild.change_voice_state(channel=None)
        await ctx.message.add_reaction("🎵")


def setup(bot):
    bot.add_cog(Music(bot))