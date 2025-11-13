import httpx
import asyncio
import dotenv
import os
import json
from datetime import datetime

from models.napcat import SendGroupMsgResponse, GetStatusResponse
from models.platform import Notice, NoticeResponse

ENV = dotenv.load_dotenv()

NAPCAT_URL = os.getenv("NAPCAT_URL")
PLATFORM_URL = os.getenv("PLATFORM_URL")
PLATFORM_LISTENING_GAME_ID = os.getenv("PLATFORM_LISTENING_GAME_ID")
PLATFORM_NOTICE_URL = f"{PLATFORM_URL}/api/game/{PLATFORM_LISTENING_GAME_ID}/notices"

NC_TOKEN = os.getenv("NAPCAT_TOKEN")
PLATFORM_COOKIE = os.getenv("PLATFORM_COOKIE")

TARGET_GROUPS = json.loads(os.getenv("TARGET_GROUPS"))  # type: ignore

GLOBAL_BOT_CLIENT = httpx.AsyncClient(
    headers={
        "User-Agent": "Luminoria-ADCTF-Bot/1.0",
        "Authorization": f"Bearer {NC_TOKEN}",
    }
)

GLOBAL_PLATFORM_CLIENT = httpx.AsyncClient(
    headers={
        "User-Agent": "Luminoria-ADCTF-Platform-Listener/1.0",
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
        "message": [
            {"type": "text", "data": {"text": message}}
        ],
    }
    try:
        resp = await GLOBAL_BOT_CLIENT.post(_url, json=payload)
        resp.raise_for_status()
        print(resp.json())
        data = SendGroupMsgResponse.model_validate(resp.json())
        if data.status != "ok":
            import traceback
            traceback.print_exc()
            print(f"Failed to send group message: {data.data.errMsg}")
            return False
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to send group message: {e}")
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
        resp.raise_for_status()
        data = NoticeResponse.model_validate(resp.json())
        return data.data
    except Exception as e:
        print(f"Failed to fetch notices: {e}")
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
                print(f"Sent notice {notice.notice_id} to group {group_id}")
            else:
                print(f"Failed to send notice {notice.notice_id} to group {group_id}")
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


async def launcher():
    alive = await check_alive()
    if not alive:
        print("Napcat service is not alive.")
        return
    else:
        print("Napcat service is alive. Start listening ADCTF notices...")

    while True:
        now = datetime.now()
        print(f"[{now:%Y-%m-%d %H:%M:%S}] Checking for new notices...")
        notices = await fetch_notices()
        unread_notices = check_unread_notice(notices)
        if unread_notices:
            await send_unread_notices_to_groups(unread_notices)
        await asyncio.sleep(5)  # 每5秒检查一次
        print(f"[{now:%Y-%m-%d %H:%M:%S}] Sleep for 5 seconds...")


if __name__ == "__main__":
    asyncio.run(launcher())
