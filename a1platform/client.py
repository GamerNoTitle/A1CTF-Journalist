from httpx import AsyncClient

from a1platform.exception import (
    PlatformException,
    CredentialsNotSatisfiedException,
    CredentialsNotSetException,
    CaptchaFailedToSolveException,
    LoginFailedException,
    GameNotFoundException,
    NoPermissionException,
    UnauthorizedAccessException,
)
from a1platform.models import (
    CaptchaResponse,
    CaptchaSubmitResponse,
    LoginResponse,
    ChallengeResponse,
    NoticeResponse,
)
from a1platform.models import Challenge as A1CTF_Challenges
from utils.captcha import solve_challenge


class PlatformClient:
    def __init__(
        self,
        base_url: str,
        game_id: int | str,
        username: str | None = None,
        password: str | None = None,
        cookie: str | None = None,
    ):
        if not all([username, password]) and not cookie:
            raise CredentialsNotSatisfiedException("You must provide username and password, or a valid cookie.")
        if all([username, password]):
            self.credential_set = True
        else:
            self.credential_set = False
        self.client = AsyncClient(base_url=base_url)
        self.game_id = game_id
        self.username = username
        self.password = password
        self.cookie = cookie
        self.challenges: list[A1CTF_Challenges] = []

    @property
    def notice_url(self) -> str:
        return f"/api/game/{self.game_id}/notices"

    @property
    def challenge_url(self) -> str:
        return f"/api/game/{self.game_id}/challenges"

    @property
    def profile_url(self) -> str:
        return "/api/account/profile"

    @property
    def captcha_challenge_url(self) -> str:
        return "/api/cap/challenge"

    @property
    def captcha_redeem_url(self) -> str:
        return "/api/cap/redeem"

    @property
    def login_url(self) -> str:
        return "/api/auth/login"

    async def match_status(self, status_code: int):
        match status_code:
            case 200:
                return
            case 403:
                raise NoPermissionException("You do not have permission to access this resource.")
            case 404:
                raise GameNotFoundException("The specified game was not found. Please check the game ID.")
            case 401:
                raise UnauthorizedAccessException("You are not authorized to access this resource.")
            case _:
                raise PlatformException(f"Unexpected response code: {status_code}")

    async def _check_cookie_valid(self) -> bool:
        resp = await self.client.get(self.profile_url)
        if resp.status_code == 200:
            return True
        return False

    async def _login_platform(self):
        if not self.credential_set:
            raise CredentialsNotSetException("Credentials are not set.")
        resp = await self.client.post(self.captcha_challenge_url)
        resp.raise_for_status()
        captcha_response = CaptchaResponse.model_validate_json(resp.content)
        solutions = solve_challenge(
            captcha_response.token,
            captcha_response.challenge.c,
            captcha_response.challenge.s,
            captcha_response.challenge.d,
        )
        resp = await self.client.post(
            self.captcha_redeem_url,
            json={"token": captcha_response.token, "solutions": solutions},
        )
        resp.raise_for_status()
        submit_response = CaptchaSubmitResponse.model_validate_json(resp.content)
        if not submit_response.success or not submit_response.token:
            raise CaptchaFailedToSolveException("Failed to solve captcha.")
        resp = await self.client.post(
            self.login_url,
            json={
                "username": self.username,
                "password": self.password,
                "captcha": submit_response.token,
            },
        )
        resp.raise_for_status()
        login_response = LoginResponse.model_validate_json(resp.content)
        if login_response.code != 200:
            raise LoginFailedException(f"Login failed: {login_response.message}")
        self.client.cookies.update({"a1token": login_response.token})  # type: ignore

    async def _sync_challenges(self):
        if not await self._check_cookie_valid():
            await self._login_platform()
        resp = await self.client.get(self.challenge_url)
        await self.match_status(resp.status_code)
        data = ChallengeResponse.model_validate_json(resp.content)
        self.challenges = data.data.challenges

    async def fetch_notice(self):
        if not await self._check_cookie_valid():
            await self._login_platform()
        resp = await self.client.get(self.notice_url)
        notices = NoticeResponse.model_validate_json(resp.content)
        await self.match_status(notices.code)
        return notices.data
