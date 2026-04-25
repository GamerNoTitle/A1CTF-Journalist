import asyncio
import dotenv
import os
import json
from utils.logger import log

from napcat.client import NapcatClient
from napcat.exception import ClientIsClosedException, NapcatException
from a1platform.client import PlatformClient
from storage import NoticeStorage

ENV = dotenv.load_dotenv()
TARGET_GROUPS = json.loads(os.getenv("TARGET_GROUPS"))  # type: ignore
NAPCAT_CLIENT = NapcatClient(os.getenv("NAPCAT_URL"), os.getenv("NAPCAT_TOKEN"))  # type: ignore
PLATFORM_CLIENT = PlatformClient(
    os.getenv("PLATFORM_URL"),  # type: ignore
    os.getenv("PLATFORM_LISTENING_GAME_ID"),    # type: ignore
    os.getenv("PLATFORM_USERNAME"),
    os.getenv("PLATFORM_PASSWORD"),
    os.getenv("PLATFORM_COOKIE"),
)
NOTICE_STORAGE = NoticeStorage("notices.json")

async def launcher():
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
    while True:
        try:
            notices = await PLATFORM_CLIENT.fetch_notice()
            if notices == NOTICE_STORAGE.notices.notices:
                await asyncio.sleep(5)
            else:
                log("[*] New notices found! Preparing to send message...")
                for notice in notices:
                    for group in TARGET_GROUPS:
                        log(f"[*] Sending notice message {str(notice)} to group {group}...")
                        try:
                            await NAPCAT_CLIENT.send_group_msg(
                                group,
                                str(notice)
                            )
                        except ClientIsClosedException:
                            global NAPCAT_CLIENT
                            log("[*] Napcat client is closed. Attempting to reconnect...")
                            NAPCAT_CLIENT = NapcatClient(os.getenv("NAPCAT_URL"), os.getenv("NAPCAT_TOKEN"))  # type: ignore
                        except NapcatException:
                            log("[*] Failed to send message to Napcat. Will retry in the next loop.")
        except KeyboardInterrupt:
            log("[*] Keyboard interrupt received. Closing Napcat client and exiting...")
            await NAPCAT_CLIENT.aclose()
            break

if __name__ == "__main__":
    asyncio.run(launcher())
