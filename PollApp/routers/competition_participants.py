from typing import Annotated

from fastapi import Depends, HTTPException, Path, status, APIRouter
from sqlmodel import Session, select

from PollApp.database import get_session
from PollApp.models import Polls, PollRequest, Competitions, CompetitionsRequest, CompetitionParticipantsRequest, \
    CompetitionParticipants
from .auth import get_current_user

router = APIRouter(
    prefix='/competitions/participant',
    tags=['competitions/participant']
)

user_dependency = Annotated[dict, Depends(get_current_user)]




@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(CompetitionParticipants)
    return session.exec(statement).all()

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