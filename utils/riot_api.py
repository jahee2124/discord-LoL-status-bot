import urllib.parse
import requests
from collections import Counter
import asyncio # 비동기 HTTP 요청을 위해 aiohttp를 사용하는 것이 더 좋지만, 여기서는 requests를 사용하므로 asyncio.to_thread를 활용
from functools import lru_cache # DDragon 데이터 캐싱용

from config.settings import RIOT_API_KEY, DEFAULT_REGION, NUM_MATCHES_TO_ANALYZE, NUM_CHAMPION_MASTERY_TO_SHOW
import discord # discord.Color 사용

# --- Constants ---
DDRAGON_BASE_URL = "https://ddragon.leagueoflegends.com"

TIER_COLORS = {
    "IRON": discord.Color.dark_gray(),
    "BRONZE": discord.Color.from_rgb(170, 85, 0), # 갈색 느낌
    "SILVER": discord.Color.light_gray(),
    "GOLD": discord.Color.gold(),
    "PLATINUM": discord.Color.from_rgb(79, 158, 158), # 청록색 느낌
    "EMERALD": discord.Color.green(), # 에메랄드 티어 추가
    "DIAMOND": discord.Color.blue(),
    "MASTER": discord.Color.purple(),
    "GRANDMASTER": discord.Color.red(),
    "CHALLENGER": discord.Color.teal(),
    "UNRANKED": discord.Color.default()
}

TIER_ICONS = {
    "IRON": "https://i.namu.wiki/i/fRDGuYd_ntkXCiaC44IrD6d-4KXNvOaiCxnv4gbxFNQbkg7_WK0iJOcFYJBPwtHxmduWquZHKSdkFMHajUucD_3anVCqWFbIbulWJLvQkZVA9UJixrL3QUmopKPjakxknIZ6Ragr4aPnv1Mor617sQ.webp",
    "BRONZE": "https://i.namu.wiki/i/VW5ehiDiNsTj9v-qIqTf4uqegHlmhGMzk0CtCaceWkH-6dtO-bfigeggTjXho6UiIUMJXUTUkJOHmI08qimZbA2pawZRu7UpezYRB6dBi73qX1ml62CNzqyq84ZB5skHoOYS22SfpKiKBPnzBfTu1Q.webp",
    "SILVER": "https://i.namu.wiki/i/TJpgPFCEF0exeNIlkGgLsKHhiKmlt3iSi4jCIAlIeB_gSgvA0xNPN2MilmqkXUBxh1mrEz2rT2EDKvn44wJrnJ-g8aXmp5osKpwHqHT0ij-H70lKPJzGCuhAuNWc7_u9OY2EK8e08R_Y6R6rTa4g7A.webp",
    "GOLD": "https://i.namu.wiki/i/Wfe40ojjHziwfyTVNP42YYSPnw6od--n2RdRWlzDawe1cnsBZl799jX8JNMLRhszO2lqtBwnv_s5-LXlyKNY4tc17jxxIqr29aJMOzt32UC59NjcEy_v_pok3xIr0S6en4WQZlNdpnMl89hjPGBpdA.webp",
    "PLATINUM": "https://i.namu.wiki/i/HP6iN5Lyg3CY2YXP_p5pGjofLy3bwsMhLyFQij_Xf18CEgBq4o38qo_LmEnKE_65vIzovQFXvSQ_hRjbOGtWE9w2Z4QARhu2V01Q30tSAdtRjhRNnUiOGQQ3y5RqtkPraKCdOF7JheoofD455H77EA.webp",
    "EMERALD": "https://i.namu.wiki/i/4w2tbKP8cwst8un23o12P0BHggGb1mhgsook9D-9xy81Y9O5NLUrXUTYVE1Uw6pNiUwlcZrECMKZpv63rRqdYtKp_peXfUy2UdSw9qtpmPHbwYYS86mh6OJi-IJlER9xV4kam2iHAvyHInUs8CRGNA.webp",
    "DIAMOND": "https://i.namu.wiki/i/a_-wpdRVfUT92SK9BQmDl9CqOZF5hmcJSvL9ALHTPlY_dt2LEbipE7D3QKRYnwtfE4zJ86ZFJFMDf4aBcW4Y0q6okFqK0DuV4n8yLhZCw9P-bYp5Wu7R0oHKNXPbZ_SGh3zHuqOeZ0pU0OQKBmX_FA.webp",
    "MASTER": "https://i.namu.wiki/i/fU1nJnI0JYvC5k-KrIhyMGlaGqVKk_PZWB3Qkyri1to_KinVdisoh3qrH1UITehG5sMBbKGdhfxBV266BRu6SFB-rhh3qsptATpsop4aiRiMl-Ksw2dL4tSrgcHZxU39tBmHY4XNBMjDeRtMY6orWg.webp",
    "GRANDMASTER": "https://i.namu.wiki/i/LRSnHGJg8fr03tjeGt_16i3ugiRuRBQrzkO_74Dl6LAEH1TySa-3yAQb1oWZXj5sHFjjwfq3iuMFXuwYXYBMkg5IJ0zJWeEDX2-evF4coc85mgkT3ihoS8nBKIHrDq7OGVUbExAtkBwcjWxK8yWHPg.webp",
    "CHALLENGER": "https://i.namu.wiki/i/7J-b-o_MHFd81loEALf1XZ_XuwCQyT5bPply5rIsKB4VfBEvhcmG3s7Gh8CBkX0IBV33_OanN9rj3sur16tbmCU3CmVkmZquk8GhJnwlOBZIhoEtvx56zU30EY5pEMBeV6I88YWcETPMNgYEEaAH5Q.webp",
    "UNRANKED": "https://i.namu.wiki/i/dHU0Ds9uINVEBhHM7oewp2OM897IQ2cipM1xJAlGn88gDEiDcyHTRMOVocoJf0unEDpjoFFr1RYhAn96dG7SnefEYMSUt0HLgkuBnJ6xEqovEDZJcLXRpj5ru_S1L7NvhBRD1Y5ItSDvDUKvQPDYBg.webp" # 임시 아이콘
}


REGION_MAPPING = {
    "kr": ["asia", "kr"], "br": ["americas", "br1"], "eune": ["europe", "eun1"],
    "euw": ["europe", "euw1"], "jp": ["asia", "jp1"], "lan": ["americas", "la1"],
    "las": ["americas", "la2"], "na": ["americas", "na1"], "oce": ["americas", "oc1"],
    "tr": ["europe", "tr1"], "ru": ["europe", "ru"], "vn": ["asia", "vn2"],
}

# --- DDragon Helper Functions ---
@lru_cache(maxsize=1) # 최신 버전 정보를 캐싱 (봇 실행 중 한 번만 호출되도록)
def get_latest_ddragon_version():
    """DDragon 최신 버전을 가져옵니다."""
    try:
        response = requests.get(f"{DDRAGON_BASE_URL}/api/versions.json")
        response.raise_for_status()
        return response.json()[0]
    except Exception as e:
        print(f"Error fetching DDragon version: {e}")
        return "14.5.1" # 예: 안정적인 버전으로 폴백 (수동 업데이트 필요할 수 있음)

@lru_cache(maxsize=128) # 챔피언 데이터를 캐싱 (챔피언 수만큼)
def get_champion_data(version):
    """특정 버전의 DDragon 챔피언 데이터를 가져옵니다."""
    try:
        response = requests.get(f"{DDRAGON_BASE_URL}/cdn/{version}/data/en_US/champion.json")
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        print(f"Error fetching DDragon champion data for version {version}: {e}")
        return {}

CHAMPION_ID_TO_NAME_MAP = {} # 챔피언 ID와 이름 매핑 캐시

async def populate_champion_id_map():
    """DDragon에서 챔피언 ID와 이름 매핑을 생성합니다."""
    global CHAMPION_ID_TO_NAME_MAP
    if CHAMPION_ID_TO_NAME_MAP: # 이미 채워져 있으면 실행 안 함
        return

    version = await asyncio.to_thread(get_latest_ddragon_version) # 동기 함수를 비동기 컨텍스트에서 실행
    champion_data_dict = await asyncio.to_thread(get_champion_data, version)

    if not champion_data_dict:
        print("Failed to populate champion ID map from DDragon.")
        return

    temp_map = {}
    for champ_name_key, champ_info in champion_data_dict.items():
        temp_map[int(champ_info['key'])] = champ_info['name']
    CHAMPION_ID_TO_NAME_MAP = temp_map
    print("Champion ID to Name map populated.")

async def get_champion_name_by_id(champion_id: int) -> str:
    """챔피언 ID로 챔피언 이름을 반환합니다. 맵이 비어있으면 채웁니다."""
    if not CHAMPION_ID_TO_NAME_MAP:
        await populate_champion_id_map()
    return CHAMPION_ID_TO_NAME_MAP.get(champion_id, "Unknown Champion")


# --- Riot API Helper Functions (기존과 유사, 일부 수정) ---
async def _make_riot_api_request(url, headers, params=None):
    """Riot API 요청을 보내고 예외 처리를 하는 헬퍼 함수 (비동기 지원)"""
    loop = asyncio.get_event_loop()
    # requests는 blocking 라이브러리이므로 asyncio.to_thread 사용
    response = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers, params=params))
    response.raise_for_status() # HTTP 에러 발생 시 예외 발생
    return response.json()

def _parse_arguments(arguments, default_region):
    args_list = arguments.strip().split()
    if not args_list:
        return None, None, "사용법: `![명령어] [닉네임#태그] [서버 (기본값 kr)]`"
    region = default_region
    riot_id_full = ""
    potential_region = args_list[-1].lower()
    if potential_region in REGION_MAPPING and len(args_list) > 1:
        region = potential_region
        riot_id_full = " ".join(args_list[:-1])
    else:
        riot_id_full = " ".join(args_list)
    if '#' not in riot_id_full:
        return None, None, f"Riot ID 형식이 올바르지 않습니다. '{riot_id_full}'에서 '#'을 찾을 수 없습니다. '이름#태그' 형식으로 입력해주세요."
    return riot_id_full, region, None

async def _get_puuid_and_summoner_info(riot_id_full, region, headers):
    """Riot ID로부터 PUUID, 소환사 ID, 레벨 등을 가져옵니다."""
    game_name, tag_line = riot_id_full.split('#', 1)
    game_name_encoded = urllib.parse.quote(game_name.strip())
    tag_line_encoded = urllib.parse.quote(tag_line.strip())
    account_region_route = REGION_MAPPING[region][0]
    platform_region_route = REGION_MAPPING[region][1]

    api_url_account = f"https://{account_region_route}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name_encoded}/{tag_line_encoded}"
    account_data = await _make_riot_api_request(api_url_account, headers)
    puuid = account_data['puuid']

    api_url_summoner = f"https://{platform_region_route}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    summoner_info = await _make_riot_api_request(api_url_summoner, headers)
    summoner_id = summoner_info['id']
    summoner_level = summoner_info['summonerLevel']
    
    return puuid, summoner_id, summoner_level, game_name, tag_line.upper(), platform_region_route, account_region_route

async def _get_league_data(summoner_id, platform_region_route, headers):
    api_url_league = f"https://{platform_region_route}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    return await _make_riot_api_request(api_url_league, headers)

async def _get_champion_masteries(puuid, platform_region_route, headers, count):
    """PUUID로 챔피언 숙련도 정보를 가져옵니다 (상위 count개)."""
    # API 엔드포인트는 platform_region_route 사용
    api_url_mastery = f"https://{platform_region_route}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top"
    params = {"count": count} # Riot API는 top 엔드포인트에서 count 파라미터를 지원하지 않을 수 있음. 전체를 받고 잘라야 할 수도.
                               # 문서를 다시 확인: /lol/champion-mastery/v4/champion-masteries/by-puuid/{encryptedPUUID} (전체)
                               # /lol/champion-mastery/v4/champion-masteries/by-puuid/{encryptedPUUID}/top (상위, count 파라미터 없음)
                               # 일단 전체를 가져와서 Python에서 슬라이싱
    
    # 수정: by-puuid/{puuid}/top은 count 파라미터가 없습니다.
    # 그냥 /by-puuid/{puuid}로 전체 숙련도를 가져와서 정렬 후 상위 n개를 선택합니다.
    api_url_mastery_all = f"https://{platform_region_route}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
    
    try:
        masteries_data = await _make_riot_api_request(api_url_mastery_all, headers)
        # championPoints 기준으로 내림차순 정렬 후 상위 count 개
        sorted_masteries = sorted(masteries_data, key=lambda x: x['championPoints'], reverse=True)
        return sorted_masteries[:count]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404: # 숙련도 정보가 없을 수 있음
            return []
        raise e # 다른 에러는 다시 발생


# --- Main Functions for Commands (get_solo_ranked_winrate는 이전과 동일하게 유지 가능) ---
async def get_solo_ranked_winrate(arguments, default_region=DEFAULT_REGION):
    # ... (이전 코드와 동일)
    riot_id_full, region, error_msg = _parse_arguments(arguments, default_region)
    if error_msg:
        return error_msg

    headers = {"X-Riot-Token": RIOT_API_KEY}

    try:
        # summonerLevel은 여기선 필요 없으므로 _ 사용
        _, summoner_id, _, game_name, tag_line, platform_region_route, _ = \
            await _get_puuid_and_summoner_info(riot_id_full, region, headers)
        league_data = await _get_league_data(summoner_id, platform_region_route, headers)

        for entry in league_data:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                wins = entry.get('wins', 0)
                losses = entry.get('losses', 0)
                total_games = wins + losses
                if total_games > 0:
                    win_rate = (wins / total_games) * 100
                    tier = entry.get('tier', 'Unranked')
                    rank = entry.get('rank', '')
                    lp = entry.get('leaguePoints', 0)
                    return f"{game_name}#{tag_line} ({region.upper()}) ({tier} {rank} {lp}LP)의 개인/2인 랭크 게임 승률: **{win_rate:.2f}%** ({wins}승 {losses}패)"
                else:
                    return f"{game_name}#{tag_line} ({region.upper()})의 이번 시즌 개인/2인 랭크 게임 기록이 없습니다."
        return f"{game_name}#{tag_line} ({region.upper()})의 이번 시즌 개인/2인 랭크 게임 기록이 없습니다."

    except requests.exceptions.HTTPError as e:
        # ... (이전 에러 처리와 동일)
        if e.response.status_code == 404:
            return f"Riot ID '{riot_id_full}' 또는 관련 데이터를 찾을 수 없습니다."
        elif e.response.status_code == 403:
            return "Riot API 키가 유효하지 않거나 접근 권한이 없습니다."
        elif e.response.status_code == 429:
            return "Riot API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        else:
            return f"API 요청 중 오류가 발생했습니다: HTTP {e.response.status_code}."
    except Exception as e:
        return f"명령어 처리 중 알 수 없는 오류가 발생했습니다: {e}"


async def get_summoner_profile_data(arguments, default_region=DEFAULT_REGION):
    riot_id_full, region, error_msg = _parse_arguments(arguments, default_region)
    if error_msg:
        return {"error": error_msg}

    headers = {"X-Riot-Token": RIOT_API_KEY}
    profile_data = {
        "riot_id_parsed": "N/A",
        "region": region.upper(),
        "summoner_level": "N/A",
        "tier_info": "개인/2인 랭크 게임 기록 없음",
        "tier_icon_url": TIER_ICONS.get("UNRANKED"),
        "embed_color": TIER_COLORS.get("UNRANKED"),
        "preferred_position": "N/A",
        "main_champions_recent": [], # 최근 게임 기반 주 챔피언
        "top_mastery_champions": [], # 숙련도 기반 주 챔피언
        "overall_kda": "N/A",
        "recent_games_analyzed": 0,
        "error": None
    }

    try:
        puuid, summoner_id, summoner_level, game_name, tag_line, platform_region_route, account_region_route = \
            await _get_puuid_and_summoner_info(riot_id_full, region, headers)
        
        profile_data["riot_id_parsed"] = f"{game_name}#{tag_line}"
        profile_data["summoner_level"] = summoner_level

        # 1. 개인/2인 랭크 게임 승률 및 티어 + 아이콘/색상
        league_data = await _get_league_data(summoner_id, platform_region_route, headers)
        solo_rank_found = False
        current_tier_name = "UNRANKED" # 기본값
        for entry in league_data:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                wins = entry.get('wins', 0)
                losses = entry.get('losses', 0)
                total_games = wins + losses
                tier = entry.get('tier', 'Unranked').upper() # 대문자로 통일
                rank = entry.get('rank', '')
                lp = entry.get('leaguePoints', 0)
                
                current_tier_name = tier if tier else "UNRANKED"

                if total_games > 0:
                    win_rate = (wins / total_games) * 100
                    profile_data["tier_info"] = f"{tier} {rank} {lp}LP ({wins}승 {losses}패, 승률: {win_rate:.2f}%)"
                else:
                    profile_data["tier_info"] = f"{tier} {rank} (배치 미완료 또는 기록 없음)"
                solo_rank_found = True
                break
        
        profile_data["tier_icon_url"] = TIER_ICONS.get(current_tier_name, TIER_ICONS["UNRANKED"])
        profile_data["embed_color"] = TIER_COLORS.get(current_tier_name, TIER_COLORS["UNRANKED"])


        # 2. 최근 NUM_MATCHES_TO_ANALYZE 경기 분석 (선호 포지션, 주 챔피언, KDA)
        match_ids = []
        try:
            match_ids_url = f"https://{account_region_route}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
            params = {"queue": 420, "count": NUM_MATCHES_TO_ANALYZE, "start": 0}
            match_ids = await _make_riot_api_request(match_ids_url, headers, params=params)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404: pass
            else: raise

        if match_ids:
            positions = []
            champions_played_recent = Counter()
            total_kills = 0
            total_deaths = 0
            total_assists = 0
            games_processed = 0

            # DDragon 챔피언 이름 맵 채우기 (아직 안 채워졌다면)
            if not CHAMPION_ID_TO_NAME_MAP:
                await populate_champion_id_map()

            for match_id in match_ids: # 병렬 처리 고려 가능 (aiohttp 사용 시)
                try:
                    match_detail_url = f"https://{account_region_route}.api.riotgames.com/lol/match/v5/matches/{match_id}"
                    match_data = await _make_riot_api_request(match_detail_url, headers)
                    
                    participant_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
                    
                    if participant_data:
                        pos = participant_data.get('individualPosition', 'N/A').upper()
                        if pos == 'INVALID': pos = participant_data.get('teamPosition', 'N/A').upper()
                        if pos not in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY', 'NONE', 'N/A', '']: pos = 'N/A'
                        if pos == 'BOTTOM': pos = 'ADC'
                        elif pos == 'UTILITY': pos = 'SUPPORT'
                        if pos != 'N/A': positions.append(pos)

                        champions_played_recent[participant_data['championName']] += 1
                        total_kills += participant_data['kills']
                        total_deaths += participant_data['deaths']
                        total_assists += participant_data['assists']
                        games_processed += 1
                except Exception as e_match:
                    print(f"Error processing match {match_id} for recent games: {e_match}")
                    continue
            
            profile_data["recent_games_analyzed"] = games_processed
            if games_processed > 0:
                if positions: profile_data["preferred_position"] = Counter(positions).most_common(1)[0][0]
                else: profile_data["preferred_position"] = "포지션 정보 부족"
                
                profile_data["main_champions_recent"] = [(champ, count) for champ, count in champions_played_recent.most_common(3)]
                
                kda_ratio_str = "Perfect KDA" if total_deaths == 0 else f"{(total_kills + total_assists) / total_deaths:.2f}:1"
                profile_data["overall_kda"] = f"{total_kills/NUM_MATCHES_TO_ANALYZE} / **{total_deaths/NUM_MATCHES_TO_ANALYZE}** / {total_assists/NUM_MATCHES_TO_ANALYZE} ({kda_ratio_str})" # D값 볼드 처리
            else: # 분석할 게임이 없는 경우
                profile_data["preferred_position"] = "최근 개인/2인 랭크 게임 기록 없음"
                profile_data["overall_kda"] = "최근 개인/2인 랭크 게임 기록 없음"
        else: # match_ids가 비어있는 경우 (API에서 404 등)
            profile_data["preferred_position"] = "최근 개인/2인 랭크 게임 기록 없음"
            profile_data["overall_kda"] = "최근 개인/2인 랭크 게임 기록 없음"


        # 3. 챔피언 숙련도 (상위 N개)
        top_masteries = await _get_champion_masteries(puuid, platform_region_route, headers, NUM_CHAMPION_MASTERY_TO_SHOW)
        if top_masteries:
            # DDragon 맵 채우기 (아직 안 채워졌다면)
            if not CHAMPION_ID_TO_NAME_MAP:
                await populate_champion_id_map()
            
            for mastery_entry in top_masteries:
                champ_id = mastery_entry['championId']
                champ_name = await get_champion_name_by_id(champ_id)
                champ_points = mastery_entry['championPoints']
                profile_data["top_mastery_champions"].append((champ_name, champ_points))
        else:
            profile_data["top_mastery_champions"] = [("정보 없음", 0)]


    except requests.exceptions.HTTPError as e:
        # ... (이전 에러 처리와 유사)
        error_message_map = {
            404: f"Riot ID '{riot_id_full}' 또는 관련 데이터를 찾을 수 없습니다.",
            403: "Riot API 키가 유효하지 않거나 접근 권한이 없습니다.",
            429: "Riot API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        }
        profile_data["error"] = error_message_map.get(e.response.status_code, f"API 요청 중 오류 발생: HTTP {e.response.status_code}.")
    except Exception as e:
        profile_data["error"] = f"명령어 처리 중 알 수 없는 오류가 발생했습니다: {e}"
        import traceback
        traceback.print_exc() # 상세 에러 로그
    
    return profile_data