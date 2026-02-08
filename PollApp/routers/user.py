from typing import Annotated

from fastapi import Depends, HTTPException, status, APIRouter
from passlib.context import CryptContext
from sqlmodel import Session, select

from PollApp.database import get_session
from PollApp.models import Users, UserChangePassword
from .auth import get_current_user

router = APIRouter(
    prefix='/user',
    tags=['user']
)

db_dependency = Annotated[Session, Depends(get_session)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get('/', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, session: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    statement = select(Users).where(Users.id == user.get('id'))
    user_model = session.exec(statement).one_or_none()
    if user_model is not None:
        return user_model
    raise HTTPException(status_code=404, detail='User not found')

@router.get('/all', status_code=status.HTTP_200_OK)
async def get_users(user: user_dependency, session: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    statement = select(Users)
    user_model = session.exec(statement).all()
    if user_model is not None:
        return user_model
    raise HTTPException(status_code=404, detail='User not found')

@router.put("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_passwords(user_change_password: UserChangePassword,
                          user: user_dependency,
                          session: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    statement = select(Users).where(Users.id == user.get('id'))
    user_model = session.exec(statement).one_or_none()
    if user_model is None:
        raise HTTPException(status_code=404, detail='User not found.')

    if not bcrypt_context.verify(user_change_password.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Error on password change.')

    user_model.hashed_password = bcrypt_context.hash(user_change_password.new_password)

    session.add(user_model)
    session.commit()
    session.refresh(user_model)