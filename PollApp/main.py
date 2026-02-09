from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from PollApp.database import create_db_and_tables
from PollApp.routers import auth, polls, admin, user, competitions, competition_participants, participant_scores
from PollApp.models import User, Competitions, CompetitionParticipants, ParticipantScores, Polls

print("🔥 FastAPI app starting...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs ONCE at startup, after uvicorn starts
    create_db_and_tables()
    yield

print("🔥 FastAPI app starting...2")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://scoring-app-fe.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

app.include_router(auth.router)
# app.include_router(polls.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(competitions.router)
app.include_router(competition_participants.router)
app.include_router(participant_scores.router)

print("🔥 FastAPI app starting...3")
