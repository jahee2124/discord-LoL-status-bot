import urllib.parse
import requests
from config.settings import RIOT_API_KEY

REGION_MAPPING = {
    "kr": ["asia", "kr"],
    "br": ["americas", "br1"],
    "eune": ["europe", "eun1"],
    "euw": ["europe", "euw1"],
    "jp": ["asia", "jp1"],
    "lan": ["americas", "la1"],
    "las": ["americas", "la2"],
    "na": ["americas", "na1"],
    "oce": ["americas", "oc1"],
    "tr": ["europe", "tr1"],
    "ru": ["europe", "ru"],
    "vn": ["asia", "vn2"],
}

async def get_solo_ranked_winrate(arguments, default_region):
    args_list = arguments.strip().split()
    if not args_list:
        return "사용법: `!승률 [닉네임#태그] [서버 (기본값 kr)]`"

    region = default_region
    riot_id_full = ""

    potential_region = args_list[-1].lower()
    if potential_region in REGION_MAPPING and len(args_list) > 1:
        region = potential_region
        riot_id_full = " ".join(args_list[:-1])
    else:
        riot_id_full = " ".join(args_list)

    if '#' not in riot_id_full:
        return f"Riot ID 형식이 올바르지 않습니다. '{riot_id_full}'에서 '#'을 찾을 수 없습니다. '이름#태그' 형식으로 입력해주세요."

    game_name, tag_line = riot_id_full.split('#', 1)
    game_name_encoded = urllib.parse.quote(game_name.strip())
    tag_line_encoded = urllib.parse.quote(tag_line.strip())

    account_region_route = REGION_MAPPING[region][0]
    platform_region_route = REGION_MAPPING[region][1]
    headers = {"X-Riot-Token": RIOT_API_KEY}

    try:
        # Account API 호출
        api_url_account = f"https://{account_region_route}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name_encoded}/{tag_line_encoded}"
        response_account = requests.get(api_url_account, headers=headers)
        response_account.raise_for_status()
        account_data = response_account.json()
        puuid = account_data['puuid']

        # Summoner API 호출
        api_url_summoner = f"https://{platform_region_route}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        response_summoner = requests.get(api_url_summoner, headers=headers)
        response_summoner.raise_for_status()
        summoner_info = response_summoner.json()
        summoner_id = summoner_info['id']

        # League API 호출
        api_url_league = f"https://{platform_region_route}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        response_league = requests.get(api_url_league, headers=headers)
        response_league.raise_for_status()
        league_data = response_league.json()

        # 솔로랭크 정보 추출
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
                    return f"{game_name}#{tag_line.upper()} ({region.upper()}) ({tier} {rank} {lp}LP)의 솔로랭크 승률: **{win_rate:.2f}%** ({wins}승 {losses}패)"
                else:
                    return f"{game_name}#{tag_line.upper()} ({region.upper()})의 이번 시즌 솔로랭크 게임 기록이 없습니다."
        return f"{game_name}#{tag_line.upper()} ({region.upper()})의 이번 시즌 솔로랭크 기록이 없습니다."

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Riot ID '{game_name}#{tag_line}'를 찾을 수 없습니다."
        elif e.response.status_code == 403:
            return "Riot API 키가 유효하지 않거나 접근 권한이 없습니다."
        elif e.response.status_code == 429:
            return "Riot API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        else:
            return f"API 요청 중 오류가 발생했습니다: HTTP {e.response.status_code}."
    except Exception as e:
        return f"명령어 처리 중 알 수 없는 오류가 발생했습니다: {e}"