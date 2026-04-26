import asyncio
import dotenv
import os
import json
import uvicorn
from fastapi import FastAPI, WebSocket
from typing import Any

from utils.logger import log
from napcat.client import NapcatClient, NapcatWebsocketServer
from a1platform.client import PlatformClient
from storage import NoticeStorage
from router import Router
from context.constant import HELP_MSG, RANK_MAPPING, ABOUT_MSG

APPLICATION = FastAPI()
NAPCAT_SERVER = NapcatWebsocketServer()

ENV = dotenv.load_dotenv()
try:
    TARGET_GROUPS = json.loads(os.getenv("TARGET_GROUPS"))  # type: ignore
except Exception as e:
    TARGET_GROUPS = os.getenv("TARGET_GROUPS", "").split(",")  # type: ignore
NAPCAT_CLIENT = NapcatClient(os.getenv("NAPCAT_URL"), os.getenv("NAPCAT_TOKEN"))  # type: ignore
PLATFORM_CLIENT = PlatformClient(
    os.getenv("PLATFORM_URL"),  # type: ignore
    os.getenv("PLATFORM_LISTENING_GAME_ID"),  # type: ignore
    os.getenv("PLATFORM_USERNAME"),
    os.getenv("PLATFORM_PASSWORD"),
    os.getenv("PLATFORM_COOKIE"),
)
NOTICE_STORAGE = NoticeStorage("notices.json")
router = Router(PLATFORM_CLIENT, NAPCAT_SERVER)


@router.register("!!help")
@router.register("!!h")
def help_handler(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!help command with params: {params}, context: {context}")
    return HELP_MSG


@router.register("!!rank")
@router.register("!!r")
async def rank_handler(params: str, context: dict[str, Any]) -> str:  # type: ignore
    log(f"[*] Received !!rank command with params: {params}, context: {context}")
    limit = -1
    start = -1
    end = -1
    if not params:
        limit = 10
    elif params.isdigit():
        limit = int(params)
    elif ":" in params:
        try:
            start_str, end_str = params.split(":")
            start = int(start_str)
            end = int(end_str)
        except ValueError:
            return "参数格式错误！请使用 !!help 获取帮助"
    # 获取排行榜数据
    scoreboard = await PLATFORM_CLIENT.fetch_scoreboard()
    if not scoreboard or not scoreboard.teams:
        return "排行榜数据暂不可用，请稍后再试！"
    # 根据参数返回对应的排行榜信息
    if limit != -1 and start == -1 and end == -1:
        # 返回前 N 名的队伍
        top_teams = scoreboard.teams[:limit]
        result = f"排行榜前 {limit} 名的队伍：\n"
        for idx, team in enumerate(top_teams, start=1):
            result += f"{RANK_MAPPING.get(team.rank, idx + 1)} {team.team_name} - {team.score} pts\n"
        return result


@router.register("!!challenge")
@router.register("!!c")
async def challenge_handler(params: str, context: dict[str, Any]) -> str:  # type: ignore
    log(f"[*] Received !!challenge command with params: {params}, context: {context}")
    challenges = await PLATFORM_CLIENT.fetch_challenges()
    if not challenges:
        return "挑战数据暂不可用，请稍后再试！"
    if params:
        param_list = params.split(maxsplit=1)
        if len(param_list) == 1 and param_list[0].lower() == "all":
            # 返回所有挑战的列表
            result = "所有挑战列表：\n"
            for challenge in challenges:
                result += f"[{challenge.category}]{challenge.challenge_name}: {challenge.cur_score} pts/{challenge.solve_count} solved\n"
            return result
        elif len(param_list) == 1:
            # 根据参数模糊匹配挑战名称
            keyword = params.strip().lower()
            matched_challenges = [
                c for c in challenges if keyword in c.challenge_name.lower()
            ]
            if not matched_challenges:
                return f"未找到匹配 '{params}' 的挑战，请检查名称是否正确！"
            result = f"匹配 '{params}' 的挑战列表：\n"
            for challenge in matched_challenges:
                result += f"[{challenge.category}]{challenge.challenge_name}: {challenge.cur_score} pts/{challenge.solve_count} solved\n"
            return result
        else:
            return "你未提供参数或提供了错误的参数！请使用 !!help 获取帮助"


@router.register("!!team")
@router.register("!!t")
async def team_handler(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!team command with params: {params}, context: {context}")
    if not params:
        return "未提供队伍名称，请使用 !!help 获取帮助"
    team_name = params.strip()
    scoreboard = await PLATFORM_CLIENT.fetch_scoreboard()
    challenges = await PLATFORM_CLIENT.fetch_challenges()
    if not scoreboard or not scoreboard.teams:
        return "排行榜数据暂不可用，请稍后再试！"
    if not challenges:
        return "题目数据暂不可用，请稍后再试！"
    matched_team = next(
        (t for t in scoreboard.teams if t.team_name.lower() == team_name.lower()), None
    )
    if not matched_team:
        return f"未找到队伍 '{team_name}'，请检查名称是否正确！"
    result = f"队伍 {matched_team.team_name} 当前得分：{matched_team.score} pts\n解题情况：\n"
    for solve in matched_team.solved_challenges:
        challenge_category = next(
            (c.category for c in challenges if c.challenge_id == solve.challenge_id),
            "未知类别",
        )
        result += (
            f"- [{challenge_category}] {solve.challenge_name} ({solve.score} pts for No.{solve.rank} solve)\n"
        )
    return result


@router.register("!!about")
def about_handler(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!about command with params: {params}, context: {context}")
    return ABOUT_MSG


@APPLICATION.websocket("/ws")
async def websocket(ws: WebSocket):
    await NAPCAT_SERVER.connect(ws)
    while True:
        data = await NAPCAT_SERVER.receive_json()
        log(f"[*] Caught napcat data: {data}")
        sender_id: int = data.get("user_id", -1)
        message_id: int = data.get("message_id", -1)
        group_id: int = data.get("group_id", -1)
        log(
            f"[*] Parsed sender_id: {sender_id}, message_id: {message_id}, group_id: {group_id}"
        )
        if sender_id == -1 or message_id == -1 or group_id == -1:
            continue
        if str(group_id) not in TARGET_GROUPS:
            continue
        message_list = data.get("message", [])
        # 如果正常获取到了消息内容
        if message_list:
            parsed_message: list[str] = []
            for message in message_list:
                if message.get("type") == "text":
                    parsed_message.append(message.get("data", {}).get("text", ""))  # type: ignore
            result_message = await router.feed(
                " ".join(parsed_message),
                {
                    "sender_id": sender_id,
                    "message_id": message_id,
                    "group_id": group_id,
                },
            )
            log(f"[*] Generated result message: {result_message}")
            if result_message:
                await NAPCAT_SERVER.send_group_msg(
                    group_id=group_id,
                    raw_message=[
                        {"type": "reply", "data": {"id": message_id}},
                        {"type": "at", "data": {"qq": sender_id}},
                        {"type": "text", "data": {"text": result_message}},
                    ],
                )
        await asyncio.sleep(0.1)


async def launcher():
    global NAPCAT_CLIENT, PLATFORM_CLIENT, NOTICE_STORAGE
    log("[+] Start launching A1CTF Journalist...")
    log(f"[*] Target groups: {','.join(TARGET_GROUPS)}")
    log("[*] Checkin Napcat service status...")
    if not await NAPCAT_CLIENT.check_alive():
        log("[*] Napcat service is not alive. Please check the connection.")
        return
    else:
        log("[*] Napcat is alive and responsible, loading config and previous cache...")
    try:
        NOTICE_STORAGE.load()
        log("[*] Successfully loaded config and cache.")
    except Exception as e:
        log(f"[-] Failed to load config and cache: {e}")


if __name__ == "__main__":
    asyncio.run(launcher())
    uvicorn.run(APPLICATION, host="0.0.0.0", port=8000)
