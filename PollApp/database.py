from sqlmodel import create_engine, SQLModel, Session

sqlite_file_name = "pollsapp5.db"
sqlite_url = f"sqlite:///PollApp/{sqlite_file_name}"

engine = create_engine(sqlite_url)

# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:Halilintar99@localhost/PollApplicationDatabase'

# engine = create_engine(SQLALCHEMY_DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session