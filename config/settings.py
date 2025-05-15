#config/settings.py
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

# 분석할 최근 경기 수
NUM_MATCHES_TO_ANALYZE = int(os.getenv("NUM_MATCHES_TO_ANALYZE", 20))

# 표시할 챔피언 숙련도 개수
NUM_CHAMPION_MASTERY_TO_SHOW = int(os.getenv("NUM_CHAMPION_MASTERY_TO_SHOW", 5)) # 기본 5개

# 디스코드 Intents 설정
INTENTS = discord.Intents.default()
INTENTS.message_content = True