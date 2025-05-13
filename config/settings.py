import discord
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 디스코드 토큰 및 Riot API 키
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")

# 기본 지역 설정
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "kr")

# 디스코드 Intents 설정
INTENTS = discord.Intents.default()
INTENTS.message_content = True