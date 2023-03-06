import logging

from bot.settings import settings

# Enable logging
logging.basicConfig(format="%(asctime)s [%(levelname)s]: %(message)s",
                    level=logging.DEBUG if settings.mode == 'DEV' else logging.INFO)
logger = logging.getLogger(__name__)
