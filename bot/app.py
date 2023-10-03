
import src.logger_config

from src.telegram_api import app, job_queue

from loguru import logger

if __name__ == "__main__":
    logger.info("Inializing complete, bot starting")
    app.run_polling()
