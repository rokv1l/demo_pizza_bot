from datetime import datetime

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, filters

from config import user_messages
from src.database import session_maker, User
from src.telegram_utils import delete_old_keyboard


async def start_callback(update: Update, context: CallbackContext) -> None:
    is_authorized = context.user_data.get("is_authorized")
    if is_authorized:
        await update.effective_chat.send_message(user_messages["start_0"])
    else:
        with session_maker() as session:
            user = (
                session.query(User)
                .filter(User.tg_id == update.effective_chat.id)
                .first()
            )
            if user and user.phone:
                context.user_data["is_authorized"] = True
                await update.effective_chat.send_message(user_messages["start_0"])
                return
        keyboard = []
        keyboard.append([KeyboardButton("Отправить контакт", request_contact=True)])
        context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
            user_messages["start_1"], reply_markup=ReplyKeyboardMarkup(keyboard)
        )


async def contact_callback(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    is_authorized = context.user_data.get("is_authorized")
    if is_authorized:
        await update.effective_chat.send_message(user_messages["start_0"])
        return
    data = update.message.contact.phone_number
    with session_maker() as session:
        user = (
            session.query(User)
            .filter(User.tg_id == update.effective_chat.id)
            .first()
        )
        if user and user.phone:
            context.user_data["is_authorized"] = True
            await update.effective_chat.send_message(user_messages["start_0"])
            return
        elif user:
            user.phone = data
            session.commit()
        else:
            user = User(
                tg_id=update.effective_chat.id,
                username=update.effective_chat.username,
                phone=data,
                created_at=datetime.now(),
            )
            session.add(user)
            session.commit()
        await update.effective_chat.send_message(
            user_messages["contact_callback_0"]
        )


start_handler = CommandHandler("start", start_callback)
contact_auth_handler = MessageHandler(filters.CONTACT, contact_callback)
