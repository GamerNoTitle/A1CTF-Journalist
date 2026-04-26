from pydantic import BaseModel, Field, UUID4
from typing import Literal, Optional
from datetime import datetime, timezone


class Notice(BaseModel):
    create_time: datetime = Field(..., alias="create_time")
    data: list[str]
    notice_category: Literal[
        "FirstBlood", "SecondBlood", "ThirdBlood", "NewAnnouncement", "NewHint"
    ]
    notice_id: int
    category: str | None = Field(None, description="challenge_category")

    def __str__(self) -> str:
        def _local_fmt(dt: datetime) -> str:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local_dt = dt.astimezone()
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")

        ts = _local_fmt(self.create_time)
        match self.notice_category:
            case "FirstBlood":
                return f"🥇 队伍 {self.data[0]} 斩获了{f' {self.category} 方向' if self.category else ''}题目 {self.data[1]} 的第一滴血！\n时间: {ts}"
            case "SecondBlood":
                return f"🥈 队伍 {self.data[0]} 斩获了{f' {self.category} 方向' if self.category else ''}题目 {self.data[1]} 的第二滴血！\n时间: {ts}"
            case "ThirdBlood":
                return f"🥉 队伍 {self.data[0]} 斩获了{f' {self.category} 方向' if self.category else ''}题目 {self.data[1]} 的第三滴血！\n时间: {ts}"
            case "NewAnnouncement":
                return f"📢 新公告发布：\n标题: {'\n'.join(self.data)}\n时间: {ts}"
            case "NewHint":
                return (
                    f"💡 题目「{self.data[0]}」发布了新提示，请前往平台查看\n时间: {ts}"
                )

    def __repr__(self) -> str:
        return f"Notice(notice_id={self.notice_id}, notice_category={self.notice_category}, created_at={self.create_time}, data={self.data})"


class NoticeResponse(BaseModel):
    code: int
    data: list[Notice]


class CaptchaChallenge(BaseModel):
    c: int
    d: int
    s: int


class CaptchaResponse(BaseModel):
    challenge: CaptchaChallenge
    expires: int
    token: str


class CaptchaSubmitResponse(BaseModel):
    expires: int
    success: bool
    token: str | None = Field(None)


class LoginResponse(BaseModel):
    code: int
    expire: str
    token: str | None = Field(None)
    message: str | None = Field(None)


class Challenge(BaseModel):
    challenge_id: int
    challenge_name: str
    total_score: int
    cur_score: int
    solve_count: int
    category: str
    visible: bool
    belong_stage: Optional[str] = Field("")


class ChallengesData(BaseModel):
    challenges: list[Challenge]


class ChallengeCache(BaseModel):
    challenges: list[Challenge] | None
    last_updated: datetime | None


class ChallengeResponse(BaseModel):
    code: int
    data: ChallengesData


class ScoreboardTimelineDot(BaseModel):
    record_time: datetime
    score: int


class ScoreboardTimeline(BaseModel):
    team_id: int
    team_name: str
    scores: list[ScoreboardTimelineDot]


class ScoreboardTeamMember(BaseModel):
    avatar: str | None
    user_name: str
    user_id: UUID4
    captain: bool


class ScoreboardSolvedChallenge(BaseModel):
    challenge_id: int
    score: int
    solver: str
    rank: int
    solve_time: datetime
    blood_reward: int
    challenge_name: str


class ScoreboardScoreAdjustment(BaseModel):
    adjustment_id: int
    adjustment_type: str
    score_change: int
    reason: str
    created_at: datetime


class ScoreboardTeam(BaseModel):
    team_id: int
    team_name: str
    team_avatar: str | None
    team_slogan: str
    team_members: list[ScoreboardTeamMember]
    team_description: str
    rank: int
    score: int
    penalty: int
    group_id: UUID4 | None
    group_name: str | None
    solved_challenges: list[ScoreboardSolvedChallenge]
    score_adjustments: list[ScoreboardScoreAdjustment]
    last_solve_time: int


class ScoreboardPagination(BaseModel):
    current_page: int
    page_size: int
    total_count: int
    total_pages: int


class ScoreboardData(BaseModel):
    game_id: int
    name: str
    top10_timelines: list[ScoreboardTimeline]
    teams: list[ScoreboardTeam]
    team_timelines: list[ScoreboardTimeline]
    challenges: list[Challenge]
    groups: list[str]
    pagination: ScoreboardPagination


class ScoreboardResponse(BaseModel):
    code: int
    data: ScoreboardData


class ScoreboardCache(BaseModel):
    board: ScoreboardData | None
    last_updated: datetime | None
