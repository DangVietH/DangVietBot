from discord.ext import commands
import discordSuperUtils
import discord
from discordSuperUtils import MusicManager


class Music(commands.Cog, discordSuperUtils.CogManager.Cog, name="Music"):
    def __init__(self, client):
        self.client = client
        self.MusicManager = MusicManager(self.client, spotify_support=False)

        super().__init__()

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        errors = {
            discordSuperUtils.NotPlaying: "Not playing any music right now...",
            discordSuperUtils.NotConnected: f"Bot not connected to a voice channel!",
            discordSuperUtils.NotPaused: "Player is not paused!",
            discordSuperUtils.QueueEmpty: "The queue is empty!",
            discordSuperUtils.AlreadyConnected: "Already connected to voice channel!",
            discordSuperUtils.QueueError: "There has been a queue error!",
            discordSuperUtils.SkipError: "There is no song to skip to!",
            discordSuperUtils.UserNotConnected: "User is not connected to a voice channel!",
            discordSuperUtils.InvalidSkipIndex: "That skip index is invalid!",
        }

        for error_type, response in errors.items():
            if isinstance(error, error_type):
                await ctx.send(response)
                return

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):
        requester = player.requester if player.requester else "Autoplay"
        thumbnail = player.data["videoDetails"]["thumbnail"]["thumbnails"][-1]["url"]

        embed = discord.Embed(
            title="Now Playing",
            color=discord.Color.random(),
            description=f"[{player.title}]({player.url})",
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"Requested by {requester}", icon_url=requester.avatar.url)
        await ctx.send(embed=embed)

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_inactivity_disconnect(self, ctx):
        await ctx.send("Left Music Channel due to inactivity")

    @commands.command(help="Leave VC")
    async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.message.add_reaction("🎵")

    @commands.command(help="See what song is currently playing")
    async def np(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            duration_played = await self.MusicManager.get_player_played_duration(
                ctx, player
            )

            await ctx.send(
                f"Currently playing: {player}, \n"
                f"Duration: {duration_played}/{player.duration}"
            )

    @commands.command(help="Join vc")
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.message.add_reaction("🎵")

    @commands.command(help="Play song or add song to queue")
    async def play(self, ctx, *, query: str):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.MusicManager.join(ctx)

        async with ctx.typing():
            players = await self.MusicManager.create_player(query, ctx.author)

        if players:
            if await self.MusicManager.queue_add(
                players=players, ctx=ctx
            ) and not await self.MusicManager.play(ctx):
                await ctx.send("Added to queue")

        else:
            await ctx.send("Query not found.")

    @commands.command(help="Pause queue")
    async def pause(self, ctx):
        if await self.MusicManager.pause(ctx):
            await ctx.message.add_reaction("🎵")

    @commands.command(help="Resume queue")
    async def resume(self, ctx):
        if await self.MusicManager.resume(ctx):
            await ctx.message.add_reaction("🎵")

    @commands.command(help="Set volume")
    async def volume(self, ctx, volume: int):
        await self.MusicManager.volume(ctx, volume)

    @commands.command(help="Looop soong")
    async def loop(self, ctx):
        await self.MusicManager.loop(ctx)
        await ctx.message.add_reaction("🎵")

    @commands.command(help="Loop queue")
    async def queueloop(self, ctx):
        await self.MusicManager.queueloop(ctx)
        await ctx.message.add_reaction("🎵")

    @commands.command(help="See queue history")
    async def history(self, ctx):
        formatted_history = [
            f"Title: '{x.title}'\nRequester: {x.requester.mention}"
            for x in (await self.MusicManager.get_queue(ctx)).history
        ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_history,
            "Song History",
            "Shows all played songs",
            25,
            string_format="{}",
        )

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()

    @commands.command(help="Skip song")
    async def skip(self, ctx, index: int = None):
        await self.MusicManager.skip(ctx, index)

    @commands.command(help="See queue")
    async def queue(self, ctx):
        formatted_queue = [
            f"**Title:** [{x.title}]({x.url})\n**Requester:** {x.requester.mention}"
            for x in (await self.MusicManager.get_queue(ctx)).queue
        ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_queue,
            "Queue",
            f"Now Playing: {await self.MusicManager.now_playing(ctx)}",
            25,
            string_format="{}",
        )

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()


def setup(client):
    client.add_cog(Music(client))
