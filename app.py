import asyncio
import dotenv
import os
import json
import uvicorn
from fastapi import FastAPI, WebSocket
from typing import Any
from contextlib import asynccontextmanager

from utils.logger import log
from napcat.client import NapcatWebsocketServer
from a1platform.client import PlatformClient
from a1platform.exception import PlatformException
from storage import NoticeStorage
from router import Router
from context.constant import HELP_MSG, RANK_MAPPING, ABOUT_MSG


@asynccontextmanager
async def lifespan(app: FastAPI):
    log("[+] Start launching A1CTF Journalist...")

    try:
        NOTICE_STORAGE.load()
        log("[*] Successfully loaded config and cache.")
    except Exception as e:
        log(f"[-] Failed to load config and cache: {e}")

    notice_task = asyncio.create_task(notice_check())
    log("[*] Background notice_check task started.")

    yield

    log("[+] Shutting down A1CTF Journalist...")

    notice_task.cancel()
    try:
        await notice_task
    except asyncio.CancelledError:
        log("[*] Background notice_check task cancelled.")


APPLICATION = FastAPI(lifespan=lifespan)
NAPCAT_SERVER = NapcatWebsocketServer()

ENV = dotenv.load_dotenv()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
raw_target_groups = os.getenv("TARGET_GROUPS", "")
if raw_target_groups.startswith("[") and raw_target_groups.endswith("]"):
    target_groups: list[str] = json.loads(raw_target_groups)
else:
    target_groups: list[str] = os.getenv("TARGET_GROUPS", "").split(",")
BASE_URL: str = os.getenv("PLATFORM_URL", "")
GAME_ID: str = os.getenv("PLATFORM_LISTENING_GAME_ID", "")
USERNAME: str = os.getenv("PLATFORM_USERNAME", "")
PASSWORD: str = os.getenv("PLATFORM_PASSWORD", "")
COOKIE: str = os.getenv("PLATFORM_COOKIE", "")
if BASE_URL == "" or GAME_ID == "":
    raise PlatformException(
        "PLATFORM_URL and PLATFORM_LISTENING_GAME_ID must be set in environment variables."
    )
PLATFORM_CLIENT = PlatformClient(
    BASE_URL,
    GAME_ID,
    USERNAME,
    PASSWORD,
    COOKIE,
)
NOTICE_STORAGE = NoticeStorage("notices.json")
router = Router(PLATFORM_CLIENT, NAPCAT_SERVER, "!!", "！！")


@router.register("help", "h")
def help_handler(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!help command with params: {params}, context: {context}")
    return HELP_MSG


@router.register("rank", "r")
async def rank_handler(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!rank command with params: {params}, context: {context}")
    limit = -1
    start = -1
    end = -1
    if not params:
        log("[*] No parameters provided for !!rank command, defaulting to top 10")
        limit = 10
    elif params.isdigit():
        log(
            f"[*] Numeric parameter provided for !!rank command: {params}, treating as limit"
        )
        limit = int(params)
    elif ":" in params:
        log(
            f"[*] Range parameter provided for !!rank command: {params}, treating as start:end"
        )
        try:
            start_str, end_str = params.split(":")
            start = int(start_str)
            end = int(end_str)
            log(f"[*] Parsed start: {start}, end: {end} for !!rank command")
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
            result += f"{RANK_MAPPING.get(team.rank, idx)} {team.team_name} - {team.score} pts\n"
        result += f"\n上次更新时间：{PLATFORM_CLIENT.scoreboard_cache.last_updated.strftime('%Y-%m-%d %H:%M:%S') if PLATFORM_CLIENT.scoreboard_cache.last_updated else '未知'}"
        return result
    elif start != -1 and end != -1:
        if start < 1 or end > len(scoreboard.teams) or start > end:
            return "排名范围参数错误！请使用 !!help 获取帮助"
        result = f"排行榜第 {start} 名到第 {end} 名的队伍：\n"
        for team in scoreboard.teams[start - 1 : end]:
            result += f"{RANK_MAPPING.get(team.rank, team.rank)} {team.team_name} - {team.score} pts\n"
        result += f"\n上次更新时间：{PLATFORM_CLIENT.scoreboard_cache.last_updated.strftime('%Y-%m-%d %H:%M:%S') if PLATFORM_CLIENT.scoreboard_cache.last_updated else '未知'}"
        return result
    else:
        return "参数错误！请使用 !!help 获取帮助"


@router.register("challenge", "c")
async def challenge_handler(params: str, context: dict[str, Any]) -> str:
    log(f"[*] Received !!challenge command with params: {params}, context: {context}")
    challenges = await PLATFORM_CLIENT.fetch_challenges()
    if not challenges:
        return "题目数据暂不可用，请稍后再试！"
    if params:
        params.strip()
        if params.lower() == "all":
            # 返回所有挑战的列表
            result = "所有题目列表：\n"
            for challenge in challenges:
                result += f"[{challenge.category}] {challenge.challenge_name}: {challenge.cur_score} pts ({challenge.solve_count} solved)\n"
        else:
            # 根据参数模糊匹配挑战名称
            keyword = params.strip().lower()
            matched_challenges = [
                c for c in challenges if keyword in c.challenge_name.lower()
            ]
            if not matched_challenges:
                return f"未找到匹配「{params}」的题目，请检查名称是否正确！"
            result = f"匹配「{params}」的题目列表：\n"
            for challenge in matched_challenges:
                result += f"[{challenge.category}] {challenge.challenge_name}: {challenge.cur_score} pts ({challenge.solve_count} solved)\n"
        result += f"\n上次更新时间：{PLATFORM_CLIENT.challenges_cache.last_updated.strftime('%Y-%m-%d %H:%M:%S') if PLATFORM_CLIENT.challenges_cache.last_updated else '未知'}"
    return "参数错误！请使用 !!help 获取帮助"


@router.register("team", "t")
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
        return f"未找到队伍「{team_name}」，请检查名称是否正确！"
    result = f"队伍 {matched_team.team_name} 当前得分：{matched_team.score} pts\n解题情况：\n"
    for solve in matched_team.solved_challenges:
        challenge_category = next(
            (c.category for c in challenges if c.challenge_id == solve.challenge_id),
            "未知类别",
        )
        result += f"- [{challenge_category}] {solve.challenge_name} ({solve.score} pts for No.{solve.rank} solve)\n"
    return result


@router.register("about")
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
        if str(group_id) not in target_groups:
            continue
        message_list = data.get("message", [])
        # 正常获取到了消息内容
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
                        {"type": "text", "data": {"text": "\n"}},
                        {"type": "text", "data": {"text": result_message}},
                    ],
                )
        await asyncio.sleep(0.1)


async def notice_check():
    while True:
        try:
            log("[*] Checking for new notices...")
            new_notices = await PLATFORM_CLIENT.fetch_notice()
            if new_notices:
                for notice in new_notices:
                    if not NOTICE_STORAGE.is_seen(notice.notice_id):
                        log(f"[*] New notice found: {notice}")
                        NOTICE_STORAGE.notices.append(notice)
                        await NAPCAT_SERVER.send_group_msg(
                            group_id=target_groups[0],  # type: ignore
                            message=str(notice),
                        )
                NOTICE_STORAGE.save()
                NOTICE_STORAGE.load()  # 刷新内存中的数据，确保状态一致
            else:
                log("[*] No new notices found.")
        except Exception as e:
            log(f"[-] Error while checking notices: {e}")
        await asyncio.sleep(10)  # 每 10 秒检查一次


if __name__ == "__main__":
    uvicorn.run(APPLICATION, host=HOST, port=PORT)
