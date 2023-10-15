from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from src.database import session_maker, User


def admin_access_control(func):
    async def inner(update: Update, context: CallbackContext):
        is_manager = context.user_data.get("is_manager")
        if is_manager:
            return await func(update, context)
        with session_maker() as session:
            user = (
                session.query(User)
                .filter(User.tg_id == update.effective_chat.id)
                .first()
            )
            if user.is_manager:
                context.user_data["is_manager"] = True
                return await func(update, context)
            else:
                return ConversationHandler.END

    return inner
