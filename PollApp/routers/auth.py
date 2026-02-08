from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from PollApp.models import User
from PollApp.database import get_session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '7d63f9b420300ea9904b923948fcedad5ca8555dc0da5ef2625c0535dba05bd8'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(SQLModel):
    username: str
    email: str
    password: str
    role: str

class Token(SQLModel):
    access_token: str
    token_type: str

def authenticate_user(username: str, password: str, session: Session = Depends(get_session)):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).one_or_none()
    if user is None:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id : int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user.')
        return {'username': username, 'id': user_id, 'role': user_role}
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')

@router.post("/")
async def create_user(create_user_request: CreateUserRequest, session: Session = Depends(get_session)):
    create_user_model = User(
        username=create_user_request.username,
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role
    )

    session.add(create_user_model)
    session.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}