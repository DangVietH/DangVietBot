import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
import discordSuperUtils


cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]


class Leveling(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.LevelingManager = discordSuperUtils.LevelingManager(client, award_role=True)
        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self):
        database = discordSuperUtils.DatabaseManager.connect(
            db
        )
        await self.LevelingManager.connect_to_database(
            database, ["xp", "roles", "role_list"]
        )

    @discordSuperUtils.CogManager.event(discordSuperUtils.LevelingManager)
    async def on_level_up(self, message, member_data, roles):
        await message.reply(
            f"You are now level {await member_data.level()}"
            + (f", you have received the {roles[0]}" f" role." if roles else "")
        )

    @commands.command(help="See your rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author  # Instead of if statement

        member_data = await self.LevelingManager.get_account(member)

        if not member_data:
            await ctx.send(f"The specified member does not have an account yet!")
            return

        guild_leaderboard = await self.LevelingManager.get_leaderboard(ctx.guild)
        leveling_member = [x for x in guild_leaderboard if x.member == member]

        image = await self.ImageManager.create_leveling_profile(
            member=member,
            member_account=member_data,
            background=discordSuperUtils.Backgrounds.GALAXY,
            rank=guild_leaderboard.index(leveling_member[0]) + 1 if leveling_member else -1,
            font_path=None,
            outline=5,
        )
        await ctx.send(file=image)

    @commands.command(help="Set role to level")
    @commands.has_permissions(administrator=True)
    async def set_roles(self, ctx, interval: int, *roles: discord.Role):
        await self.LevelingManager.set_interval(ctx.guild, interval)
        await self.LevelingManager.set_roles(ctx.guild, roles)

        await ctx.send(f"Successfully set the interval to {interval} and role list to {', '.join(role.name for role in roles)}")

    @commands.command(help="See server leaderboard")
    async def leaderboard(self, ctx):
        guild_leaderboard = await self.LevelingManager.get_leaderboard(ctx.guild)
        formatted_leaderboard = [
            f"Member: {x.member.mention}, XP: {await x.xp()}" for x in guild_leaderboard
        ]

        await discordSuperUtils.PageManager(
            ctx,
            discordSuperUtils.generate_embeds(
                formatted_leaderboard,
                title="Leveling Leaderboard",
                fields=25,
                description=f"Leaderboard of {ctx.guild}",
            ),
        ).run()


def setup(client):
    client.add_cog(Leveling(client))
