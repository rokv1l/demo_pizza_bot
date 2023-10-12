from sqlalchemy import desc
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
)

from . import states
from config import user_messages
from .utils import user_access_control
from src.database import session_maker, Order
from src.telegram_utils import delete_old_keyboard


async def orders_history_send_msg(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    index = context.user_data["history_index"]
    text = context.user_data["orders_history"][index]
    keyboard = [
        [
            InlineKeyboardButton("<", callback_data="<"),
            InlineKeyboardButton(">", callback_data=">"),
        ]
    ]
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@user_access_control
async def orders_history_entry_point(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    tg_id = update.effective_chat.id
    with session_maker() as session:
        orders = (
            session.query(Order)
            .filter(Order.tg_id == tg_id)
            .order_by(desc(Order.created_at))
            .all()
        )
        context.user_data["history_index"] = 0
        context.user_data["orders_history"] = []
        for order in orders:
            text = f"Создан в {order.created_at.date()}\n\n"
            text += "Позиции заказа:\n"
            total_cost = 0
            for product in order.basket:
                text += f"{product[0]['name']} {product[1]} штук\n"
                total_cost += product[0]["cost"]
            text += f"\nИтоговая цена: {total_cost} руб."
            context.user_data["orders_history"].append(text)
    await orders_history_send_msg(update, context)
    return states.ORDERS_HISTORY_COURUSEL


async def orders_history_swap_page_callback(
    update: Update, context: CallbackContext
) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    data = update.callback_query.data
    index = context.user_data["history_index"]
    if data == "<":
        if index <= 0:
            context.user_data["history_index"] = (
                len(context.user_data["orders_history"]) - 1
            )
        else:
            context.user_data["history_index"] += 1
    elif data == ">":
        if index >= len(context.user_data["orders_history"]) - 1:
            context.user_data["history_index"] = 0
        else:
            context.user_data["history_index"] += 1
    await orders_history_send_msg(update, context)


async def history_exit_callback(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    await update.effective_chat.send_message(user_messages["history_exit_callback_0"])
    return ConversationHandler.END


orders_history_handler = ConversationHandler(
    entry_points=[CommandHandler("history", orders_history_entry_point)],
    states={
        states.ORDERS_HISTORY_COURUSEL: [
            CallbackQueryHandler(orders_history_swap_page_callback, r"\<|\>"),
        ]
    },
    fallbacks=[CallbackQueryHandler(history_exit_callback, r"exit")],
)
