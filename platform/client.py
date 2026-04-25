from httpx import AsyncClient

from platform.exception import (
    CredentialsNotSatisfiedException,
    CredentialsNotSetException,
    CaptchaFailedToSolveException,
    LoginFailedException,
    GameNotFoundException,
    NoPermissionException,
    UnauthorizedAccessException,
)
from platform.models import (
    CaptchaResponse,
    CaptchaSubmitResponse,
    LoginResponse,
    ChallengeResponse,
    NoticeResponse,
)
from platform.models import Challenge as A1CTF_Challenges
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
        if not all([username, password]) or cookie:
            raise CredentialsNotSatisfiedException
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

    async def _check_cookie_valid(self) -> bool:
        resp = await self.client.get(self.profile_url)
        resp.raise_for_status()
        if resp.status_code == 200:
            return True
        return False

    async def _login_platform(self):
        if not self.credential_set:
            raise CredentialsNotSetException
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
            raise CaptchaFailedToSolveException
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
            raise LoginFailedException
        self.client.cookies.update({"a1token", login_response.token})  # type: ignore

    async def _sync_challenges(self):
        if not await self._check_cookie_valid():
            await self._login_platform()
        resp = await self.client.get(self.challenge_url)
        resp.raise_for_status()
        data = ChallengeResponse.model_validate_json(resp.content)
        self.challenges = data.data.challenges

    async def fetch_notice(self):
        if not await self._check_cookie_valid():
            await self._login_platform()
        resp = await self.client.get(self.notice_url)
        notices = NoticeResponse.model_validate_json(resp.content)
        match notices.code:
            case 403:
                raise NoPermissionException
            case 404:
                raise GameNotFoundException
            case 401:
                raise UnauthorizedAccessException
        return notices.data
