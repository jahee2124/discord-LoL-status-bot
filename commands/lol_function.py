import discord
from discord.ext import commands
from utils.riot_api import get_solo_ranked_winrate, get_summoner_profile_data, populate_champion_id_map # populate 추가
from config.settings import DEFAULT_REGION, NUM_MATCHES_TO_ANALYZE, NUM_CHAMPION_MASTERY_TO_SHOW

class LoLCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cog가 로드될 때 챔피언 ID 맵을 미리 채워넣도록 설정 가능
        # asyncio.create_task(populate_champion_id_map()) # 백그라운드에서 실행

    @commands.Cog.listener()
    async def on_ready(self):
        """봇이 준비되면 DDragon 데이터를 미리 로드합니다."""
        print("LoLCommands Cog 로드됨. DDragon 챔피언 데이터 로딩 시도...")
        await populate_champion_id_map() # 봇 준비 시점에 DDragon 맵 채우기

    @commands.command(name='승률')
    async def get_ranked_solo_winrate_command(self, ctx, *, arguments: str):
        await ctx.typing()
        result_message = await get_solo_ranked_winrate(arguments, DEFAULT_REGION)
        await ctx.send(result_message)

    @commands.command(name='전적')
    async def get_summoner_profile_command(self, ctx, *, arguments: str):
        await ctx.typing()
        profile_data = await get_summoner_profile_data(arguments, DEFAULT_REGION)

        if profile_data.get("error"):
            await ctx.send(profile_data["error"])
            return

        embed = discord.Embed(
            title=f"{profile_data['riot_id_parsed']} ({profile_data['region']})님의 전적",
            color=profile_data['embed_color'] # 티어별 색상 적용
        )
        
        if profile_data['tier_icon_url']:
            embed.set_thumbnail(url=profile_data['tier_icon_url']) # 티어 아이콘 적용
        
        embed.add_field(name="**레벨**", value=str(profile_data['summoner_level']), inline=True)
        embed.add_field(name="**개인/2인 랭크 게임**", value=profile_data['tier_info'], inline=False) # 한 줄 전체 사용
        
        analysis_note = f"(최근 {profile_data['recent_games_analyzed']} 게임)" if profile_data['recent_games_analyzed'] > 0 else ""
        
        embed.add_field(name=f"**선호 포지션** {analysis_note}", value=profile_data['preferred_position'], inline=True)
        # K/D/A에서 D는 utils/riot_api.py에서 이미 볼드 처리됨
        embed.add_field(name=f"**평균 K/D/A** {analysis_note}", value=profile_data['overall_kda'], inline=True)
        
        # 최근 게임 기반 주요 챔피언
        if profile_data['main_champions_recent']:
            champions_value = ""
            for champ, count in profile_data['main_champions_recent']:
                champions_value += f"{champ} ({count}회)\n"
            embed.add_field(name=f"**플레이한 챔피언 {analysis_note}**", value=champions_value.strip(), inline=False)
        else:
            embed.add_field(name=f"**플레이한 챔피언 {analysis_note}**", value="정보 없음", inline=False)

        # 숙련도 높은 챔피언
        if profile_data['top_mastery_champions'] and profile_data['top_mastery_champions'][0][0] != "정보 없음":
            mastery_value = ""
            for champ_name, points in profile_data['top_mastery_champions']:
                mastery_value += f"{champ_name} ({points:,}점)\n" # 점수에 콤마 추가
            embed.add_field(name=f"**챔피언 숙련도 TOP {NUM_CHAMPION_MASTERY_TO_SHOW}**", value=mastery_value.strip(), inline=False)
        else:
            embed.add_field(name=f"**챔피언 숙련도 TOP {NUM_CHAMPION_MASTERY_TO_SHOW}**", value="숙련도 정보 없음", inline=False)
        
        await ctx.send(embed=embed)