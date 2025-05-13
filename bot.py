import discord
from discord.ext import commands
from config.settings import DISCORD_TOKEN, INTENTS
from commands.basic_function import GeneralCommands
from commands.lol_function import LoLCommands  # lol_function.py가 존재한다고 가정

# 봇 초기화
bot = commands.Bot(command_prefix='.', intents=INTENTS)

# Cog 등록을 비동기 함수로 처리
async def load_cogs():
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(LoLCommands(bot))

@bot.event
async def on_ready():
    print(f"봇이 준비되었습니다! 로그인: {bot.user}")
    print(f"로드된 Cog: {list(bot.cogs.keys())}")

# 봇 실행
if __name__ == "__main__":
    async def main():
        async with bot:
            await load_cogs()  # Cog 로드
            await bot.start(DISCORD_TOKEN)  # 봇 실행

    import asyncio
    asyncio.run(main())