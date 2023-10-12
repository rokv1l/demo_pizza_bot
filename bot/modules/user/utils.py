from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext

from config import user_messages
from src.database import session_maker, User


def user_access_control(func):
    async def inner(update: Update, context: CallbackContext):
        is_authorized = context.user_data.get("is_authorized")
        if is_authorized:
            return func(update, context)
        with session_maker() as session:
            user = (
                session.query(User)
                .filter(User.tg_id == update.effective_chat.id)
                .first()
            )
            if user.phone:
                return await func(update, context)
            else:
                keyboard = []
                keyboard.append(
                    KeyboardButton("Отправить контакт", request_contact=True)
                )
                await update.effective_chat.send_message(
                    user_messages["user_access_control_0"],
                    reply_markup=ReplyKeyboardMarkup(keyboard),
                )

    return inner
