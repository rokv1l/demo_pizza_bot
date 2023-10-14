from loguru import logger

async def error_callback(update, context):
    logger.exception(context.error)
