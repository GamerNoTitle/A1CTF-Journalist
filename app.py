import asyncio
import dotenv
import os
import json
import uvicorn
from fastapi import FastAPI, WebSocket
from typing import Any

from utils.logger import log
from napcat.client import NapcatClient, NapcatWebsocketServer
from napcat.exception import ClientIsClosedException, NapcatException
from a1platform.client import PlatformClient
from storage import NoticeStorage
from router import Router
from context.constant import HELP_MSG, RANK_MAPPING

APPLICATION = FastAPI()
NAPCAT_SERVER = NapcatWebsocketServer()

ENV = dotenv.load_dotenv()
TARGET_GROUPS = json.loads(os.getenv("TARGET_GROUPS"))  # type: ignore
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
def get_help(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!help command with params: {params}, context: {context}")
    return HELP_MSG


@router.register("!!rank")
async def get_rank(params: str, context: dict[str, Any]) -> str:
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
            return "你提供了错误的参数！请使用 !!rank (limit=10)/(start:end) 的格式"
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
            result += f"{RANK_MAPPING.get(team.rank, idx+1)}. {team.team_name} - {team.score} pts\n"
        return result


@APPLICATION.websocket("/ws")
async def websocket(ws: WebSocket):
    await NAPCAT_SERVER.connect(ws)
    while True:
        data = await NAPCAT_SERVER.receive_json()
        log(f"[*] Caught napcat data: {data}")
        sender_id: int = data.get("user_id", -1)
        message_id: int = data.get("message_id", -1)
        group_id: int = data.get("group_id", -1)
        log(f"[*] Parsed sender_id: {sender_id}, message_id: {message_id}, group_id: {group_id}")
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
            result_message = await router.feed(" ".join(parsed_message), {"sender_id": sender_id, "message_id": message_id, "group_id": group_id})
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