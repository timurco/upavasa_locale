# Enable relative imports https://fortierq.github.io/python-import/
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parents[1]))

from bot.models import Base
from bot.services.database import engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
