from collections import defaultdict
from random import shuffle
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status, APIRouter
from sqlmodel import Session, select, func, and_
from sqlalchemy.orm import selectinload, outerjoin

from PollApp.database import get_session
from PollApp.models import Polls, PollRequest, Competitions, CompetitionsRequest, CompetitionParticipants, \
    CompetitionRead, CompetitionParticipantsRequest, ParticipantTotalScore, ParticipantScores, Users, \
    ParticipantScoreResponse
from .auth import get_current_user

router = APIRouter(
    prefix='/competitions',
    tags=['competitions']
)

user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_competition(
    competition_request: CompetitionsRequest,
    user: user_dependency,
    session: Session = Depends(get_session)
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )

    competition_model = Competitions(
        **competition_request.model_dump(),
        creator_id=user.get("id")
    )

    session.add(competition_model)
    session.commit()
    session.refresh(competition_model)

    return {
        "id": competition_model.id,
        "message": "Competition created successfully"
    }


@router.get("/", status_code=200)
async def read_all(
    user: user_dependency,
    session: Session = Depends(get_session),
):
    if user is None:
        raise HTTPException(status_code=401)

    has_polled_subquery = (
        select(ParticipantScores.id)
        .where(
            ParticipantScores.competition_id == Competitions.id,
            ParticipantScores.scorer_id == user["id"],
        )
        .exists()
    )

    statement = (
        select(
            Competitions,
            has_polled_subquery.label("has_polled")
        )
        .join(
            CompetitionParticipants,
            CompetitionParticipants.competition_id == Competitions.id
        )
        .where(CompetitionParticipants.user_id == user["id"])
    )

    rows = session.exec(statement).all()

    has_been_polled = []
    not_yet_voted = []

    for competition, has_polled in rows:
        if has_polled:
            has_been_polled.append(competition)
        else:
            not_yet_voted.append(competition)

    return {
        "has_been_polled": has_been_polled,
        "not_yet_voted": not_yet_voted,
    }

@router.get("/all", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(Competitions)
    return session.exec(statement).all()

@router.get("/{competition_id}", status_code=status.HTTP_200_OK)
async def read_competition(
    user: user_dependency,
    competition_id: Annotated[int, Path(gt=0)],
    session: Session = Depends(get_session)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

    statement = (
        select(Competitions)
        .where(Competitions.id == competition_id)
        .options(selectinload(Competitions.participants).selectinload(CompetitionParticipants.user))
    )

    competition = session.exec(statement).one_or_none()

    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )

    return {
        "competitions": {
            "id": competition.id,
            "title": competition.title,
            "desc": competition.desc,
            "participants": [
                {
                    "id": participant.id,
                    "user_id": participant.user.id if participant.user else None,
                    "username": participant.user.username if participant.user else None
                }
                for participant in competition.participants
            ]
        }
    }

@router.post("/{competition_id}/participant/add", status_code=status.HTTP_201_CREATED)
async def add_competition_participants(
    competition_id: int,
    competition_participant_request: CompetitionParticipantsRequest,
    user: user_dependency,
    session: Session = Depends(get_session)
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )

    # ✅ Check competition exists
    competition = session.get(Competitions, competition_id)
    if competition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )

    # ✅ Check creator
    if competition.creator_id != user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only competition creator can add participants"
        )

    # ✅ Create participant rows
    participants = [
        CompetitionParticipants(
            competition_id=competition_id,
            user_id=user_id
        )
        for user_id in competition_participant_request.user_ids
    ]

    session.add_all(participants)
    session.commit()

    return {
        "message": "Participants added successfully",
        "count": len(participants)
    }



@router.get(
    "/{competition_id}/scores",
    status_code=status.HTTP_200_OK
)
async def get_all_scores_by_competition(
    competition_id: int,
    user: user_dependency,
    session: Session = Depends(get_session),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

    statement = (
        select(
            ParticipantScores.scored_id,
            Users.username,
            ParticipantScores.score,
            ParticipantScores.feedback,
        )
        .join(Users, Users.id == ParticipantScores.scored_id)
        .where(ParticipantScores.competition_id == competition_id)
    )

    results = session.exec(statement).all()

    grouped: dict[int, dict] = defaultdict(
        lambda: {
            "scores": [],
            "feedbacks": [],
            "total_score": 0,
        }
    )

    for scored_id, username, score, feedback in results:
        grouped[scored_id]["id"] = scored_id
        grouped[scored_id]["username"] = username
        grouped[scored_id]["scores"].append(score)
        grouped[scored_id]["feedbacks"].append(feedback)
        grouped[scored_id]["total_score"] += score

    for data in grouped.values():
        shuffle(data["scores"])
        shuffle(data["feedbacks"])

    return list(grouped.values())

#
# @router.get("/{poll_id}", status_code=status.HTTP_200_OK)
# async def read_poll(user: user_dependency, poll_id: Annotated[int, Path(title="The ID of the poll to get", gt=0)], session: Session = Depends(get_session)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
#
#     statement = select(Polls).where(Polls.id == poll_id).where(Polls.poll_by_id == user.get('id'))
#     results = session.exec(statement)
#     poll_model = results.one_or_none()
#     if poll_model is not None:
#         return poll_model
#     raise HTTPException(status_code=404, detail='Poll not found')
#
#
# @router.put("/poll/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def update_poll(poll_id: Annotated[int, Path(title="The ID of the poll to update", gt=0)],
#                       poll_request: PollRequest,
#                       user: user_dependency,
#                       session: Session = Depends(get_session)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
#
#     statement = select(Polls).where(Polls.id == poll_id).where(Polls.poll_by_id == user.get('id'))
#     poll_model = session.exec(statement).one_or_none()
#     if poll_model is None:
#         raise HTTPException(status_code=404, detail='Poll not found.')
#
#     poll_model.name = poll_request.name
#     poll_model.poll_by = poll_request.poll_by
#     poll_model.poll = poll_request.poll
#     session.add(poll_model)
#     session.commit()
#     session.refresh(poll_model)
#
#
# @router.delete("/poll/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_poll(poll_id: Annotated[int, Path(title="The ID of the poll to delete", gt=0)],
#                       user: user_dependency,
#                       session: Session = Depends(get_session)):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
#
#     statement = select(Polls).where(Polls.id == poll_id).where(Polls.poll_by_id == user.get('id'))
#     poll_model = session.exec(statement).one_or_none()
#     if poll_model is None:
#         raise HTTPException(status_code=404, detail='Poll not found.')
#     session.delete(poll_model)
#     session.commit()
#     return None