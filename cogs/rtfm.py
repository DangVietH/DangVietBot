import warnings

import discord
import utils.rtfm_utils as rtfm
from discord.ext import commands

# directly taken and modify from https://github.com/BruceCodesGithub/OG-Robocord/blob/main/cogs/rtfm.py


class RTFM(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.targets = {
            "python": "https://docs.python.org/3",
            "discord.py": "https://discordpy.readthedocs.io/en/latest/",
            "pycord": "https://pycord.readthedocs.io/en/master/",
            "nextcord": "https://nextcord.readthedocs.io/en/latest/",
            "praw": "https://praw.readthedocs.io/en/latest",
            "asyncpraw": "https://apraw.readthedocs.io/en/latest",
            "pymongo": "https://pymongo.readthedocs.io/en/stable/",
            "motor": "https://motor.readthedocs.io/en/stable/",
            "django": "https://django.readthedocs.io/en/stable",
            "flask": "https://flask.palletsprojects.com/en/1.1.x"
        }
        self.aliases = {
            ("py", "py3", "python3", "python"): "python",
            ("dpy", "discord.py", "d.py"): "discord.py",
            ("pycord", "pyc", "py-cord"): "pycord",
            ("nextcord", "nxc"): "nextcord",
            ("reddit", "praw", "pr"): "praw",
            ("asyncpraw", "apraw", "apr"): "asyncpraw",
            ("pmongo", "pmg", "pymongo"): "pymongo",
            ("mt", "motor"): "motor",
            ("django", "dj"): "django",
            ("flask", "fl"): "flask"
        }
        self.cache = {}

    @property
    def session(self):
        return self.client.http._HTTPClient__session

    async def build(self, target) -> None:
        url = self.targets[target]
        req = await self.session.get(url + "/objects.inv")
        if req.status != 200:
            warnings.warn(
                Warning(
                    f"Received response with status code {req.status} when trying to build RTFM cache for {target} through {url}/objects.inv"
                )
            )
            raise commands.CommandError("Failed to build RTFM cache")
        self.cache[target] = rtfm.SphinxObjectFileReader(
            await req.read()
        ).parse_object_inv(url)

    @commands.command(help="available modules")
    async def rtfm_list(self, ctx):
        aliases = {v: k for k, v in self.aliases.items()}
        embed = discord.Embed(title="List of available modules", color=discord.Color.green())
        embed.description = "\n".join(
            [
                "[{0}]({1}): {2}".format(
                    target,
                    link,
                    "\u2800".join([f"`{i}`" for i in aliases[target] if i != target]),
                )
                for target, link in self.targets.items()
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(help='Search through docs')
    async def rtfm(self, ctx, docs: str, *, term: str = None):
        docs = docs.lower()
        target = None
        for aliases, target_name in self.aliases.items():
            if docs in aliases:
                target = target_name

        if not target:
            lis = "\n".join(
                [f"{index}. {value}" for index, value in list(self.targets.keys())]
            )
            return await ctx.reply(
                embed=ctx.error(
                    title="Invalid Documentation",
                    description=f"Documentation {docs} is invalid. Must be one of \n{lis}",
                )
            )
        if not term:
            return await ctx.reply(self.targets[target])

        cache = self.cache.get(target)
        if not cache:
            await ctx.trigger_typing()
            await self.build(target)
            cache = self.cache.get(target)

        results = rtfm.finder(
            term, list(cache.items()), key=lambda x: x[0], lazy=False
        )[:10]

        if not results:
            return await ctx.reply(
                f"No results found when searching for {term} in {docs}"
            )

        await ctx.reply(
            embed=discord.Embed(
                title=f"Best matches for {term} in {docs}",
                description="\n".join([f"[`{key}`]({url})" for key, url in results]),
                color=discord.Color.green(),
            )
        )


def setup(client):
    client.add_cog(RTFM(client))
