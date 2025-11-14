import httpx
import asyncio
import dotenv
import os
import json
from datetime import datetime
from utils.logger import log

from models.napcat import SendGroupMsgResponse, GetStatusResponse
from models.platform import (
    Notice,
    NoticeResponse,
    CaptchaResponse,
    CaptchaSubmitResponse,
    LoginResponse,
)

from utils.captcha import solve_challenge

ENV = dotenv.load_dotenv()

NAPCAT_URL = os.getenv("NAPCAT_URL")
PLATFORM_URL = os.getenv("PLATFORM_URL")
PLATFORM_LISTENING_GAME_ID = os.getenv("PLATFORM_LISTENING_GAME_ID")
PLATFORM_NOTICE_URL = f"{PLATFORM_URL}/api/game/{PLATFORM_LISTENING_GAME_ID}/notices"

NC_TOKEN = os.getenv("NAPCAT_TOKEN")
PLATFORM_USERNAME = os.getenv("PLATFORM_USERNAME")
PLATFORM_PASSWORD = os.getenv("PLATFORM_PASSWORD")
PLATFORM_COOKIE = os.getenv("PLATFORM_COOKIE")

TARGET_GROUPS = json.loads(os.getenv("TARGET_GROUPS"))  # type: ignore

GLOBAL_BOT_CLIENT = httpx.AsyncClient(
    headers={
        "User-Agent": "A1CTF-Journalist/1.0",
        "Authorization": f"Bearer {NC_TOKEN}",
    }
)

GLOBAL_PLATFORM_CLIENT = httpx.AsyncClient(
    headers={
        "User-Agent": "A1CTF-Journalist/1.0",
        "Cookie": PLATFORM_COOKIE,  # type: ignore
    }
)


async def send_group_message(group_id: str, message: str) -> bool:
    """
    发送单条群消息
    :param group_id: 目标群号
    :param message: 消息内容，支持多条消息合并发送
    :return: 发送是否成功
    """
    _url = f"{NAPCAT_URL}/send_group_msg"
    payload = {
        "group_id": group_id,
        "message": [{"type": "text", "data": {"text": message}}],
    }
    try:
        resp = await GLOBAL_BOT_CLIENT.post(_url, json=payload)
        resp.raise_for_status()
        log(json.dumps(resp.json(), ensure_ascii=False))
        data = SendGroupMsgResponse.model_validate(resp.json())
        if data.status != "ok":
            import traceback

            traceback.print_exc()
            log(f"Failed to send group message: {data.data.errMsg}")
            return False
        return True
    except Exception as e:
        import traceback

        traceback.print_exc()
        log(f"Failed to send group message: {e}")
        return False


async def check_alive() -> bool:
    """
    检查 Napcat 服务是否存活
    :return: 服务是否存活
    """
    _url = f"{NAPCAT_URL}/get_status"
    try:
        resp = await GLOBAL_BOT_CLIENT.post(_url)
        resp.raise_for_status()
        data = GetStatusResponse.model_validate(resp.json())
        return data.status == "ok"
    except Exception:
        return False


async def fetch_notices() -> list[Notice]:
    """
    获取目标比赛的公告列表
    :return: 公告列表
    """
    try:
        resp = await GLOBAL_PLATFORM_CLIENT.get(PLATFORM_NOTICE_URL)
        match resp.status_code:
            case 403:
                log(
                    "No permission to access notices. Probably the game has not started yet."
                )
                return []
            case 401:
                await login_platform()
                if not await check_platform_cookie_valid():
                    raise RuntimeError(
                        "Unauthorized access to notices and re-login failed. Please check your credentials."
                    )
                return []
            case 404:
                log(
                    "The game cannot be found. Please check PLATFORM_LISTENING_GAME_ID."
                )
                return []
        resp.raise_for_status()
        data = NoticeResponse.model_validate(resp.json())
        return data.data
    except Exception as e:
        log(f"Failed to fetch notices: {e}")
        return []


def check_unread_notice(notices: list[Notice]) -> list[Notice]:
    """
    检查未读公告
    :param notices: 公告列表
    :return: 未读公告列表
    """
    try:
        with open("read_notices.txt", "r") as f:
            read_ids = set(int(line.strip()) for line in f.readlines())
    except FileNotFoundError:
        read_ids = set()

    unread_notices = [notice for notice in notices if notice.notice_id not in read_ids]
    unread_notices.sort(key=lambda x: x.created_at)
    return unread_notices


async def send_unread_notices_to_groups(unread_notices: list[Notice]) -> None:
    """
    发送未读公告到目标群
    :param unread_notices: 未读公告列表
    """
    for notice in unread_notices:
        message = str(notice)
        success_flag = []
        for group_id in TARGET_GROUPS:
            success = await send_group_message(group_id, message)
            success_flag.append(success)
            if success:
                log(f"Sent notice {notice.notice_id} to group {group_id}")
            else:
                log(f"Failed to send notice {notice.notice_id} to group {group_id}")
        if all(success_flag):
            mark_notice_as_read(notice.notice_id)


def mark_notice_as_read(notice_id: int) -> bool:
    """
    标记公告为已读，并保存到文件做存储
    :param notice_id: 公告 ID
    :return: 标记是否成功
    """
    with open("read_notices.txt", "a") as f:
        f.write(f"{notice_id}\n")
    return True


async def check_platform_cookie_valid() -> bool:
    """
    检查 Platform Cookie 是否有效
    :return: Cookie 是否有效
    """
    log("Checking Platform cookie validity...")
    try:
        resp = await GLOBAL_PLATFORM_CLIENT.get(f"{PLATFORM_URL}/api/account/profile")
        resp.raise_for_status()
        if resp.status_code == 200:
            log("Platform cookie is valid.")
            return True
        log("Platform cookie is invalid.")
        return False
    except Exception as e:
        log(f"Error while checking Platform cookie validity: {e}")
        return False


async def login_platform():
    """
    登录 A1CTF 平台，并更新 Cookie 配置
    """
    if PLATFORM_USERNAME and PLATFORM_PASSWORD:
        log("Logging into Platform...")
        resp = await GLOBAL_BOT_CLIENT.post(f"{PLATFORM_URL}/api/cap/challenge")
        resp.raise_for_status()
        captcha_response = CaptchaResponse.model_validate(resp.json())
        solutions = solve_challenge(
            captcha_response.token,
            captcha_response.challenge.c,
            captcha_response.challenge.s,
            captcha_response.challenge.d,
        )
        log(f"Solved CAPTCHA challenges: {solutions}")
        resp = await GLOBAL_BOT_CLIENT.post(
            f"{PLATFORM_URL}/api/cap/redeem",
            json={"token": captcha_response.token, "solutions": solutions},
        )
        resp.raise_for_status()
        log("Submitted CAPTCHA solutions and redeemed token.")
        captcha_submit_response = CaptchaSubmitResponse.model_validate(resp.json())
        if not captcha_submit_response.success or not captcha_submit_response.token:
            raise RuntimeError("Failed to solve CAPTCHA and login to Platform")
        resp = await GLOBAL_PLATFORM_CLIENT.post(
            f"{PLATFORM_URL}/api/auth/login",
            json={
                "username": PLATFORM_USERNAME,
                "password": PLATFORM_PASSWORD,
                "captcha": captcha_submit_response.token,
            },
        )
        resp.raise_for_status()
        log("Logged into Platform successfully.")
        login_response = LoginResponse.model_validate(resp.json())
        if login_response.code != 200:
            raise RuntimeError(f"Failed to login to Platform: {login_response.message}")
        GLOBAL_PLATFORM_CLIENT.headers["Cookie"] = f"a1token={login_response.token}"
        # Set new cookie to .env and replace old one
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("PLATFORM_COOKIE="):
                    f.write(f"PLATFORM_COOKIE=a1token={login_response.token}\n")
                else:
                    f.write(line)
    else:
        raise RuntimeError("Platform username or password not set in environment.")


async def launcher():
    alive = await check_alive()
    if not alive:
        log("Napcat service is not alive.")
        return
    else:
        log("Napcat service is alive. Start listening A1CTF notices...")

        if not await check_platform_cookie_valid():
            await login_platform()
            if not await check_platform_cookie_valid():
                log("Failed to login to Platform. Exiting...")
                return
            else:
                log("Successfully logged into Platform.")

    while True:
        now = datetime.now()
        log("Checking for new notices...")
        notices = await fetch_notices()
        unread_notices = check_unread_notice(notices)
        if unread_notices:
            await send_unread_notices_to_groups(unread_notices)
        await asyncio.sleep(5)  # 每5秒检查一次
        log("Sleep for 5 seconds...")


if __name__ == "__main__":
    asyncio.run(launcher())
