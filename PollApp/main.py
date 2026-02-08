from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from PollApp.database import create_db_and_tables
from PollApp.routers import auth, polls, admin, user, competitions, competition_participants, participant_scores

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs ONCE at startup, after uvicorn starts
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
# app.include_router(polls.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(competitions.router)
app.include_router(competition_participants.router)
app.include_router(participant_scores.router)
