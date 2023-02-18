from bot.models import Base
from bot.services.database import engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)