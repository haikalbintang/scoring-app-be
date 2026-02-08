from typing import List

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public'}

    id: int | None = Field(default=None, primary_key=True)
    email: str
    username: str = Field(min_length=1, index=True, unique=True)
    hashed_password: str
    role: str

    competitions: List["CompetitionParticipants"] = Relationship(back_populates="user")

class UserRequest(SQLModel):
    email: str
    username: str = Field(min_length=1)
    hashed_password: str
    role: str

class UserChangePassword(SQLModel):
    password: str
    new_password: str = Field(min_length=1)


class Competitions(SQLModel, table=True):
    __table_args__ = {'schema': 'public'}

    id: int | None = Field(default=None, primary_key=True)
    title: str
    desc: str
    creator_id: int

    participants: List["CompetitionParticipants"] = Relationship(back_populates="competition")

class CompetitionsRequest(SQLModel):
    title: str
    desc: str

class CompetitionParticipants(SQLModel, table=True):
    __tablename__ = "competition_participants"
    __table_args__ = {'schema': 'public'}

    id: int | None = Field(default=None, primary_key=True)

    competition_id:  int = Field(foreign_key="public.competitions.id")
    user_id: int = Field(foreign_key="public.users.id")

    competition: "Competitions" = Relationship(back_populates="participants")
    user: "User" = Relationship(back_populates="competitions")

class CompetitionParticipantsRequest(SQLModel):
    user_ids: List[int]

class ParticipantScores(SQLModel, table=True):
    __tablename__ = "participant_scores"
    __table_args__ = {'schema': 'public'}

    id: int | None = Field(default=None, primary_key=True)
    competition_id: int = Field(foreign_key="public.competitions.id")
    scorer_id: int = Field(foreign_key="public.users.id")
    scored_id: int = Field(foreign_key="public.users.id")
    score: int
    feedback: str

    competition: "Competitions" = Relationship()
    scorer: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ParticipantScores.scorer_id]"}
    )
    scored: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ParticipantScores.scored_id]"}
    )

class ScoreRequest(SQLModel):
    score: int
    feedback: str

class Polls(SQLModel, table=True):
    __table_args__ = {'schema': 'public'}

    id: int | None = Field(default=None, primary_key=True)
    name: str
    poll_by: str
    poll: int
    poll_by_id: int | None = Field(default=None, foreign_key="public.users.id")

class PollRequest(SQLModel):
    name: str = Field(min_length=1)
    poll_by: str = Field(min_length=1)
    poll: int = Field(gt=0, le=1000)


class ParticipantRead(SQLModel):
    id: int
    name: str

class CompetitionRead(SQLModel):
    id: int
    title: str
    participants: List[ParticipantRead] = []

class ParticipantTotalScore(SQLModel):
    scored_id: int
    username: str
    total_score: int
    scores: list[int]
    feedbacks: list[str]

class ScoreItem(SQLModel):
    participant_id: int
    score: int
    feedback: str | None = None

class BulkScoreRequest(SQLModel):
    polls: list[ScoreItem]

class ParticipantScoreResponse(SQLModel):
    id: int
    scored_id: int
    username: str
    score: int
    feedback: str | None