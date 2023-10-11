
import src.logger_config
import src.db_init

from loguru import logger

from src.telegram_api import app
from modules import user


if __name__ == "__main__":
    logger.info("Inializing complete, bot starting")
    app.add_handler(user.start_handler)
    app.add_handler(user.menu_handler)
    app.run_polling()
