from typing import Annotated

from fastapi import Depends, HTTPException, Path, status, APIRouter
from sqlmodel import Session, select

from PollApp.database import get_session
from PollApp.models import Polls, PollRequest
from .auth import get_current_user

router = APIRouter(
    prefix='/polls',
    tags=['polls']
)

user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(Polls).where(Polls.poll_by_id == user.get('id'))
    return session.exec(statement).all()


@router.get("/poll/{poll_id}", status_code=status.HTTP_200_OK)
async def read_poll(user: user_dependency, poll_id: Annotated[int, Path(title="The ID of the poll to get", gt=0)], session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(Polls).where(Polls.id == poll_id).where(Polls.poll_by_id == user.get('id'))
    results = session.exec(statement)
    poll_model = results.one_or_none()
    if poll_model is not None:
        return poll_model
    raise HTTPException(status_code=404, detail='Poll not found')


@router.post("/poll", status_code=status.HTTP_201_CREATED)
async def create_poll(poll_request: PollRequest, user: user_dependency,
                      session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    poll_model = Polls(**poll_request.model_dump(), poll_by_id=user.get('id'))
    session.add(poll_model)
    session.commit()


@router.put("/poll/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_poll(poll_id: Annotated[int, Path(title="The ID of the poll to update", gt=0)],
                      poll_request: PollRequest,
                      user: user_dependency,
                      session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(Polls).where(Polls.id == poll_id).where(Polls.poll_by_id == user.get('id'))
    poll_model = session.exec(statement).one_or_none()
    if poll_model is None:
        raise HTTPException(status_code=404, detail='Poll not found.')

    poll_model.name = poll_request.name
    poll_model.poll_by = poll_request.poll_by
    poll_model.poll = poll_request.poll
    session.add(poll_model)
    session.commit()
    session.refresh(poll_model)


@router.delete("/poll/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poll(poll_id: Annotated[int, Path(title="The ID of the poll to delete", gt=0)],
                      user: user_dependency,
                      session: Session = Depends(get_session)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(Polls).where(Polls.id == poll_id).where(Polls.poll_by_id == user.get('id'))
    poll_model = session.exec(statement).one_or_none()
    if poll_model is None:
        raise HTTPException(status_code=404, detail='Poll not found.')
    session.delete(poll_model)
    session.commit()
    return None