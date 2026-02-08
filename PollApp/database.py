from sqlmodel import create_engine, SQLModel, Session

# sqlite_file_name = "pollsapp5.db"
# sqlite_url = f"sqlite:///PollApp/{sqlite_file_name}"
#
# engine = create_engine(sqlite_url)

# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:Halilintar99@localhost/PollApplicationDatabase'
SQLALCHEMY_DATABASE_URL = 'postgresql://scoring_app_wentwhich:77c0c98b804ac621263126cf1325e9ab46b9a709@1-59hp.h.filess.io:5434/scoring_app_wentwhich'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
    "options": "-csearch_path=public"
})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session