import asyncio
import re
import aiohttp
import async_timeout
import discord
import wavelink
from discord.ext import commands
from discord.ext.commands.errors import CheckFailure


class NotConnectedToVoice(CheckFailure):
    pass


class PlayerNotConnected(CheckFailure):
    pass


class MustBeSameChannel(CheckFailure):
    pass


def voice_connected():
    def predicate(ctx):
        try:
            ctx.author.voice.channel
            return True
        except AttributeError:
            raise NotConnectedToVoice("You are not connected to a vc")

    return commands.check(predicate)


def player_connected():
    def predicate(ctx):
        player: WebPlayer = ctx.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if not player.is_connected:
            raise PlayerNotConnected("I'm not connected to any vc")
        return True

    return commands.check(predicate)


def in_same_channel():
    def predicate(ctx):
        player: WebPlayer = ctx.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if not player.is_connected:
            raise PlayerNotConnected("I'm not connected to any vc")

        try:
            return player.channel_id == ctx.author.voice.channel.id
        except:
            raise MustBeSameChannel(
                "Please join to the channel where I'm connected."
            )

    return commands.check(predicate)


class WebPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = asyncio.Queue()
        self.loop = "NONE"  # CURRENT, PLAYLIST
        self.currently_playing = None
        self.bound_channel = None
        self.controller_message = None
        self.player_is_invoking = False

    async def destroy(self, *, force: bool = False) -> None:
        player_message = self.controller_message

        if player_message:
            try:
                await player_message.delete()
            except:
                pass

        return await super().destroy(force=force)

    async def do_next(self) -> None:
        if self.is_playing:
            return

        try:
            self.waiting = True
            with async_timeout.timeout(300):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            # No music has been played for 5 minutes, cleanup and disconnect...
            return await self.destroy()

        self.currently_playing = track
        await self.play(track)
        await self.invoke_player()

    async def invoke_player(self) -> None:
        if self.player_is_invoking:
            return

        self.player_is_invoking = True

        player_message = self.controller_message

        if player_message:
            try:
                await player_message.delete()
            except:
                pass

        track = self.current

        embed = discord.Embed(
            title="Now playing", description=f"[{track.title}]({track.uri})", color=discord.Color(0x2F3136)
        )

        embed.set_thumbnail(url=track.thumb)
        embed.add_field(
            name="Length",
            value=f"{int((self.position / 1000) // 60)}:{int((self.position / 1000) % 60)}/{int((track.length / 1000) // 60)}:{int((track.length / 1000) % 60)}",
        )
        embed.add_field(name="Looping", value=self.loop)
        embed.add_field(name="Volume", value=self.volume)

        next_song = ""

        if self.loop == "CURRENT":
            next_song = self.current.title
        else:
            if len(self.queue._queue) > 0:
                next_song = self.queue._queue[0].title

        if next_song:
            embed.add_field(name="Next Song", value=next_song, inline=False)

        self.controller_message = await self.bound_channel.send(embed=embed)
        self.bot.after_controller = 0
        self.player_is_invoking = False


def not_playing_anything():
    return "I'm not playing anything right now"


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_REG = re.compile(r"https?://(?:www\.)?.+")
        if not hasattr(self.bot, "wavelink"):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        await self.bot.wavelink.initiate_node(
            host="lavalink.darrennathanael.com",
            port=2095,
            rest_uri="http://lavalink.darrennathanael.com:2095",
            password="whatwasthelastingyousaid",
            identifier="MAIN",
            region="singapore",
        )

        for guild in self.bot.guilds:
            if guild.me.voice:
                player: WebPlayer = self.bot.wavelink.get_player(guild.id, cls=WebPlayer)
                try:
                    await player.connect(guild.me.voice.channel.id)
                    print(f"Connected to existing voice -> {guild.me.voice.channel.id}")
                except Exception as e:
                    print(e)

    @commands.command(help='Join vc', aliases=["connect"])
    @voice_connected()
    async def join(self, ctx):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if player.is_connected:
            if not player.bound_channel:
                player.bound_channel = ctx.channel

            if player.channel_id == ctx.channel.id:
                return await ctx.send(
                    "I'm already connected to your vc"
                )

            return await ctx.send(
                "I'm not connected to another vc so I can't join this one"
            )

        channel = ctx.author.voice.channel
        self.bot.voice_users[ctx.author.id] = channel.id

        msg = await ctx.send(f"Connecting to **`{channel.name}`**")
        await player.connect(channel.id)
        player.bound_channel = ctx.channel
        await msg.edit(
            content=f"Connected to **`{channel.name}`** and bounded to {ctx.channel.mention}"
        )

    @commands.command(help="Leave VC", aliases=["disconnect"])
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def leave(self, ctx):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)
        await player.destroy()

    @commands.command(help="Play music")
    @voice_connected()
    async def play(self, ctx, *, query):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if not player.is_connected:
            await ctx.invoke(self.join)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}.",
            )

        msg = await ctx.send(f"Searching for `{query}` 🔎")
        query = query.strip("<>")
        if not self.URL_REG.match(query):
            # SoundCloud searching is possible by prefixing "scsearch:" instead.
            query = f"ytsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(query)

        if not tracks:
            return await msg.edit(content="Could not find any song with that query.")

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                await player.queue.put(track)

            msg.edit(
                content=f'Added the playlist **{tracks.data["playlistInfo"]["name"]}** with **{len(tracks.tracks)}** songs to the queue.'
            )
        else:
            await player.queue.put(tracks[0])

            await msg.edit(content=f"Added **{str(tracks[0])}** to the queue.")

        if not player.is_playing:
            await player.do_next()

    @commands.command(help="Skip music")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def skip(self, ctx):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        current_loop = player.loop
        player.loop = "NONE"

        await player.stop()

        if current_loop != "CURRENT":
            player.loop = current_loop

    @commands.command(help="Pause player")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def pause(self, ctx):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        if player.is_playing:
            if player.is_paused:
                return await ctx.send("Player is already paused.")

            await player.set_pause(pause=True)
            await ctx.message.add_reaction("🎵")

        await ctx.send(not_playing_anything())

    @commands.command(help="Resume player")
    @player_connected()
    @voice_connected()
    @in_same_channel()
    async def resume(self, ctx):
        """Resume the player"""
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        if player.is_playing:
            if not player.is_paused:
                return await ctx.send("Player is not paused.")

            await player.set_pause(pause=False)
            await ctx.message.add_reaction("🎵")

        await ctx.send(not_playing_anything())

    @commands.command(help="Seek the player backward or forward")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def seek(self, ctx, seconds: int, reverse: bool = False):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        if player.is_playing:
            if not player.is_paused:
                if not reverse:
                    new_position = player.position + (seconds * 1000)
                    if new_position > player.current.length:
                        new_position = player.current.length
                else:
                    new_position = player.position - (seconds * 1000)
                    if new_position < 0:
                        new_position = 0

                await player.seek(new_position)
                return await ctx.send(f"Player has been seeked {seconds} seconds.")

            return await ctx.send(
                "Player is paused. Resume the player to use this command."
            )

        await ctx.send(not_playing_anything())

    @commands.command(help="Set volume")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def volume(self, ctx, vol: int, forced=False):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        if vol < 0:
            return await ctx.send("Volume can't be less than 0")

        if vol > 100 and not forced:
            return await ctx.send("Volume can't greater than 100")

        await player.set_volume(vol)
        await ctx.message.add_reaction("🎵")

    @commands.command(help="Loop song or queue")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def loop(self, ctx, type: str):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        valid_types = ["NONE", "CURRENT", "PLAYLIST"]
        type = type.upper()

        if type not in valid_types:
            return await ctx.send("Loop type must be `NONE`, `CURRENT` or `PLAYLIST`.")

        if len(player.queue._queue) < 1 and type == "PLAYLIST":
            return await ctx.send(
                "There must be 2 songs in the queue in order to use the PLAYLIST loop"
            )

        if not player.is_playing:
            return await ctx.send("Player is not playing any track. Can't loop")

        player.loop = type

        await ctx.send(f"Player is now looping `{type}`")

    @commands.command(help="See what song I'm playing")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def np(self, ctx):
        """What's playing now?"""
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        if not player.current:
            return await ctx.send(not_playing_anything())

        await player.invoke_player()

    @commands.command(aliases=["q"], help="See current queue")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def queue(self, ctx):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        queue = player.queue._queue
        if len(queue) < 1:
            return await ctx.send("Nothing is in the queue.")

        embed = discord.Embed(color=discord.Color(0x2F3136))
        embed.set_author(name="Queue", icon_url="https://cdn.discordapp.com/attachments/900197917170737152/912229731766796368/unknown.png")

        tracks = ""
        if player.loop == "CURRENT":
            next_song = f"Next > [{player.current.title}]({player.current.uri}) \n\n"
        else:
            next_song = ""

        if next_song:
            tracks += next_song

        for index, track in enumerate(queue):
            tracks += f"{index + 1}. [{track.title}]({track.uri}) \n"

        embed.description = tracks

        await ctx.send(embed=embed)

    @commands.command(help="Set equalizer")
    @voice_connected()
    @player_connected()
    @in_same_channel()
    async def equalizer(self, ctx):
        player: WebPlayer = self.bot.wavelink.get_player(ctx.guild.id, cls=WebPlayer)

        if ctx.channel != player.bound_channel:
            return await ctx.send(
                f"Player is bounded to {player.bound_channel.mention}", delete_after=5
            )

        eqs = {
            "1️⃣": ["Flat", wavelink.eqs.Equalizer.flat()],
            "2️⃣": ["Boost", wavelink.eqs.Equalizer.boost()],
            "3️⃣": ["Metal", wavelink.eqs.Equalizer.metal()],
            "4️⃣": ["Piano", wavelink.eqs.Equalizer.piano()],
        }

        embed = discord.Embed(color=discord.Color(0x2F3136))
        embed.description = f"Current Eq - **{player.eq.name}**\n\n1. Flat \n2. Boost\n3. Metal\n4. Piano"
        embed.set_author(icon_url="https://cdn.discordapp.com/attachments/900197917170737152/912230052844941312/unknown.png", name="Select Equalizer")

        msg = await ctx.send(embed=embed)

        await msg.add_reaction("1️⃣")
        await msg.add_reaction("2️⃣")
        await msg.add_reaction("3️⃣")
        await msg.add_reaction("4️⃣")

        def check(reaction, user):
            return (
                reaction.message.id == msg.id
                and user.id == ctx.author.id
                and reaction.emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0, check=check
                )
            except:
                await msg.delete()
                break

            selected_eq = eqs[reaction.emoji][1]
            await player.set_equalizer(selected_eq)

            embed.description = (
                f"Current Eq - **{eqs[reaction.emoji][0]}**\n\n"
                "1. Flat \n2. Boost\n3. Metal\n4. Piano"
            )

            await msg.edit(embed=embed)

    @commands.command(help="Search lyrics")
    async def lyric(self, ctx, query: str = None):
        if not query:
            player: WebPlayer = self.bot.wavelink.get_player(
                ctx.guild.id, cls=WebPlayer
            )
            if not player.is_playing:
                return await ctx.send(
                    "Nothing is playing. Either play a song to see its lyrics or type a song name while using this command"
                )

            title = player.current.title

        else:
            title = query

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://some-random-api.ml/lyrics?title={title}"
            ) as response:
                song_data = await response.json()
                if song_data:
                    lyrics = song_data["lyrics"]

        lines = [line.replace("\n", "") for line in lyrics.split("\n")]
        pages = []

        stack = ""
        for line in lines:
            new_stack = stack + line + "\n"
            if len(new_stack) > 300:
                pages.append(stack)
                stack = ""
            stack += line + "\n"

        if not pages:
            pages.append(stack)

        embed = discord.Embed(title=f"{song_data['author']}/{song_data['title']}")
        embed.description = pages[0]
        try:
            embed.set_thumbnail(url=song_data["thumbnail"]["genius"])
        except:
            pass

        if len(pages) == 1:
            return await ctx.send(embed=embed)

        else:
            current_page = 0
            embed.set_footer(text=f"{current_page + 1}/{len(pages)}")

            book: discord.Message = await ctx.send(embed=embed)
            buttons = ["◀️", "▶️"]

            for emoji in buttons:
                await book.add_reaction(emoji)

            await asyncio.sleep(1)
            while True:
                reaction, reaction_user = await self.bot.wait_for(
                    "reaction_add", timeout=180
                )

                if reaction.emoji == "◀️":
                    current_page -= 1
                    if current_page < 0:
                        current_page = 0
                        continue

                elif reaction.emoji == "▶️":
                    current_page += 1

                try:
                    await book.remove_reaction(reaction.emoji, reaction_user)
                except:
                    pass

                try:
                    content = pages[current_page]
                except:
                    current_page -= 1
                    continue

                embed.description = content
                embed.set_footer(text=f"{current_page + 1}/{len(pages)}")
                await book.edit(embed=embed)


class MusicEvents(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bot.players = {}
        self.bot.voice_users = {}
        self.bot.after_controller = 0

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        player: WebPlayer = self.bot.wavelink.get_player(
            message.guild.id, cls=WebPlayer
        )

        if not player.is_playing:
            return

        if player.bound_channel != message.channel:
            return

        self.bot.after_controller += 1

        if self.bot.after_controller > 5:
            if player.is_connected and player.is_playing:
                player_message = player.controller_message
                if not player_message:
                    return

                await player.invoke_player()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        player: WebPlayer = self.bot.wavelink.get_player(member.guild.id, cls=WebPlayer)

        if member.id == self.bot.user.id:
            if before.channel and after.channel:
                if before.channel != after.channel:
                    await player.destroy()
                    await player.connect(after.channel.id)

        if after.channel:
            for voice_member in after.channel.members:
                self.bot.voice_users[voice_member.id] = {
                    "channel": after.channel.id,
                    "player": player,
                }
        else:
            try:
                self.bot.voice_users.pop(member.id)
            except:
                pass

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node: wavelink.Node, payload):
        if payload.player.loop == "CURRENT":
            return await payload.player.play(payload.player.currently_playing)

        if payload.player.loop == "PLAYLIST":
            await payload.player.queue.put(payload.player.currently_playing)

        await payload.player.do_next()


def setup(bot):
    bot.add_cog(Music(bot))
    bot.add_cog(MusicEvents(bot))