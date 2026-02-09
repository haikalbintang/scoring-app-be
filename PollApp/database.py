from sqlmodel import create_engine, SQLModel, Session
import os
from dotenv import load_dotenv

load_dotenv()

# sqlite_file_name = "pollsapp6.db"
# sqlite_url = f"sqlite:///PollApp/{sqlite_file_name}"
#
# engine = create_engine(sqlite_url)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# SQLALCHEMY_DATABASE_URL = 'postgresql://scoring_app_wentwhich:77c0c98b804ac621263126cf1325e9ab46b9a709@1-59hp.h.filess.io:5434/scoring_app_wentwhich?options=-c%20search_path=public'

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
    "options": "-csearch_path=public"
})


def create_db_and_tables():
    from PollApp.models import User, Competitions, CompetitionParticipants, ParticipantScores, Polls

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session