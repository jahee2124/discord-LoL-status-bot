from discord.ext import commands
from utils.riot_api import get_solo_ranked_winrate
from config.settings import DEFAULT_REGION

class LoLCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='승률')
    async def get_ranked_solo_winrate(self, ctx, *, arguments: str):
        """
        [닉네임#태그] [서버(기본값 kr)] - 시즌 솔로랭크 승률을 보여줍니다.
        """
        result_message = await get_solo_ranked_winrate(arguments, DEFAULT_REGION)
        await ctx.send(result_message)