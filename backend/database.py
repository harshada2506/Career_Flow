from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://careeruser:StrongPassword123@localhost:5432/careerflow"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

# ✅ REQUIRED FOR FASTAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()