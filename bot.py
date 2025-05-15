#bot.py
import discord
from discord.ext import commands
from config.settings import DISCORD_TOKEN, INTENTS
# from commands.basic_function import GeneralCommands # basic_function.py가 실제로 있다면 주석 해제
from commands.lol_function import LoLCommands
from commands.basic_function import GeneralCommands

# 봇 초기화
bot = commands.Bot(command_prefix='.', intents=INTENTS) # 접두사 일관성 확인

# Cog 등록을 비동기 함수로 처리
async def load_cogs():
    # if 'GeneralCommands' not in bot.cogs: # basic_function.py가 실제로 있다면 주석 해제
    #     await bot.add_cog(GeneralCommands(bot))
    if 'LoLCommands' not in bot.cogs: # 중복 로딩 방지
        await bot.add_cog(LoLCommands(bot))
    if 'GeneralCommands' not in bot.cogs: # 중복 로딩 방지
        await bot.add_cog(GeneralCommands(bot))
@bot.event
async def on_ready():
    print(f"봇이 준비되었습니다! 로그인: {bot.user}")
    # Cog 로드는 main 함수에서 호출되므로, 여기서는 로드된 Cog 목록을 보여주는 것이 더 적합
    # await load_cogs() # 여기서 호출하는 것보다 main에서 호출하는 것이 일반적
    print(f"로드된 Cog: {list(bot.cogs.keys())}")
    # 봇이 준비된 후, LoLCommands의 on_ready 리스너가 DDragon 데이터를 로드할 것임

# 봇 실행
if __name__ == "__main__":
    async def main():
        async with bot:
            await load_cogs() # Cog 로드
            await bot.start(DISCORD_TOKEN)

    import asyncio
    asyncio.run(main())