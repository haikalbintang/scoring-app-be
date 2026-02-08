from typing import Annotated

from fastapi import Depends, HTTPException, Path, status, APIRouter
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from PollApp.database import get_session
from PollApp.models import Polls, PollRequest, Competitions, CompetitionsRequest, CompetitionParticipantsRequest, \
    CompetitionParticipants, ParticipantScores, ScoreRequest, BulkScoreRequest
from .auth import get_current_user

router = APIRouter(
    prefix='/competitions/participant/score',
    tags=['competitions/participant/score']
)

user_dependency = Annotated[dict, Depends(get_current_user)]




@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(ParticipantScores)
    return session.exec(statement).all()

@router.post("/create/{comp_id}/{scored_id}", status_code=status.HTTP_201_CREATED)
async def create_score(
    competition_request: ScoreRequest,
    comp_id: int,
    scored_id: int,
    user: user_dependency,
    session: Session = Depends(get_session),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )

    existing_score = session.exec(
        select(ParticipantScores).where(
            ParticipantScores.competition_id == comp_id,
            ParticipantScores.scorer_id == user.get("id"),
            ParticipantScores.scored_id == scored_id
        )
    ).first()

    if existing_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a score for this user in this competition"
        )

    if user.get('id') == scored_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot score yourself"
        )

    competition = session.get(Competitions, comp_id)
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )

    participant = session.exec(
        select(CompetitionParticipants)
        .where(
            CompetitionParticipants.competition_id == comp_id,
            CompetitionParticipants.user_id == scored_id
        )
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a participant of this competition"
        )

    score_model = ParticipantScores(
        **competition_request.model_dump(),
        competition_id=comp_id,
        scored_id=scored_id,
        scorer_id=user.get('id')
    )

    try:
        session.add(score_model)
        session.commit()
        session.refresh(score_model)
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create score"
        )

    return score_model


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poll(participant_id: Annotated[int, Path(title="The ID of the participant to delete", gt=0)],
                      user: user_dependency,
                      session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(CompetitionParticipants).where(CompetitionParticipants.id == participant_id)
    participant_model = session.exec(statement).one_or_none()
    if participant_model is None:
        raise HTTPException(status_code=404, detail='Poll not found.')
    session.delete(participant_model)
    session.commit()
    return None

@router.post("/bulk-create/{competition_id}")
async def bulk_create_scores(
    competition_id: int,
    request: BulkScoreRequest,
    user: user_dependency,
    session: Session = Depends(get_session),
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 1. Validate payload
    if not request.polls:
        raise HTTPException(status_code=400, detail="Empty poll list")

    total_score = sum(p.score for p in request.polls)
    if total_score > 1000:
        raise HTTPException(
            status_code=400,
            detail="Total score must be less than 1000"
        )

    # 2. Authorization check (example)
    is_allowed = session.exec(
        select(CompetitionParticipants)
        .where(
            CompetitionParticipants.competition_id == competition_id,
            CompetitionParticipants.user_id == user.get('id'),
        )
    ).first()

    if not is_allowed:
        raise HTTPException(status_code=403, detail="Not allowed to score")

    # 3. Prepare bulk insert
    rows = [
        ParticipantScores(
            competition_id=competition_id,
            scored_id=p.participant_id,
            score=p.score,
            feedback=p.feedback,
            scorer_id=user.get('id'),
        )
        for p in request.polls
    ]

    # 4. Transaction-safe commit
    try:
        session.add_all(rows)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit scores")

    return {
        "status": "ok",
        "count": len(rows),
    }

