import os
from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, Request
from jose import JWTError
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

SECRET_KEY = os.getenv("SECRET_KEY")
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

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get('sub')
        user_id: str = payload.get('id')
        role: str = payload.get('role')

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return {
            "username": username,
            "id": user_id,
            "role": role,
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


# async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get('sub')
#         user_id : int = payload.get('id')
#         user_role: str = payload.get('role')
#         if username is None or user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail='Could not validate user.')
#         return {'username': username, 'id': user_id, 'role': user_role}
#     except InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail='Could not validate user.')

def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token)
    return payload

@router.post("/register")
async def create_user(response: Response, create_user_request: CreateUserRequest, session: Session = Depends(get_session)):
    user = User(
        username=create_user_request.username,
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    access_token = create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=20),
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # ⚠️ set False in local development
        samesite="lax",
        max_age=20 * 60,
        path="/",
    )

    return {"message": "User created successfully"}


@router.post("/token")
async def login_for_access_token(response: Response,
                                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 remember: bool = Form(False),
                                 session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')

    # -----------------------------
    # Expiration Logic
    # -----------------------------
    if remember:
        expire_minutes = 60 * 24 * 30  # 30 days
    else:
        expire_minutes = 20  # 20 minutes

    access_token = create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=expire_minutes),
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # ⚠️ set False in local development
        samesite="lax",
        max_age=expire_minutes * 60,
        path="/",
    )
    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    return {"message": "Logged out successfully"}