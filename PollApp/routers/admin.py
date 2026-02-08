from typing import Annotated

from fastapi import Depends, Path, HTTPException, status, APIRouter
from sqlmodel import Session, select

from PollApp.database import get_session
from PollApp.models import Polls
from .auth import get_current_user

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)

db_dependency = Annotated[Session, Depends(get_session)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/poll", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, session: db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    statement = select(Polls)
    return session.exec(statement).all()


@router.delete("/poll/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(poll_id: Annotated[int, Path(title="The ID of the poll to delete", gt=0)],
                      user: user_dependency,
                      session: db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    poll_model = session.exec(select(Polls).where(Polls.id == poll_id)).one_or_none()
    if poll_model is None:
        raise HTTPException(status_code=404, detail='Poll not found.')
    session.delete(poll_model)
    session.commit()
    return