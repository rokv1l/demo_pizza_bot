
import src.logger_config
import src.db_init

from loguru import logger

from src.telegram_api import app
from modules.errors_module import error_callback
from modules import user


if __name__ == "__main__":
    logger.info("Inializing complete, bot starting")
    app.add_handler(user.start_handler)
    app.add_handler(user.menu_handler)
    app.add_handler(user.contact_auth_handler)
    app.add_handler(user.orders_history_handler)
    app.add_error_handler(error_callback)
    app.run_polling()
