from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.settings import settings
from bot.models import Base

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(engine)

db = SessionLocal()

# Uncomment for recreating database
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
