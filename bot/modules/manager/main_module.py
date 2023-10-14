from loguru import logger
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext,
    filters,
)

from . import states
from config import admin_messages
from .utils import admin_access_control
from src.database import session_maker, Order, User
from src.telegram_utils import delete_old_keyboard


@admin_access_control
async def admin_entry_point(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    keyboard = [
        [
            InlineKeyboardButton(
                "Написать сообщение пользователю", callback_data="send_message"
            )
        ]
    ]
    keyboard.append(
        [InlineKeyboardButton("Управление заказами", callback_data="manage_orders")]
    )
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        admin_messages["admin_entry_point_0"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return states.ADMIN_ACTION


async def send_message_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    keyboard = [[InlineKeyboardButton("Выход", callback_data="exit")]]
    if update.callback_query:
        context.user_data["target_user"] = None
        await update.effective_chat.send_message(
            admin_messages["send_message_callback_0"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return states.SEND_MESSAGE_ASK_TEXT
    elif not context.user_data.get("target_user"):
        tg_id = update.message.text
        with session_maker() as session:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if not user:
                await update.effective_chat.send_message(
                    admin_messages["send_message_callback_1"],
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
                return
            else:
                context.user_data["target_user"] = tg_id
        await update.effective_chat.send_message(
            admin_messages["send_message_callback_2"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return states.SEND_MESSAGE
    else:
        text = update.message.text
        bot = update.get_bot()
        try:
            await bot.send_message(chat_id=context.user_data["target_user"], text=text)
            await update.effective_chat.send_message(
                admin_messages["send_message_callback_3"]
            )
        except Exception as e:
            logger.exception(e)
            await update.effective_chat.send_message(
                admin_messages["send_message_callback_4"]
            )
        return await admin_entry_point(update, context)


async def orders_send_message(update: Update, context: CallbackContext) -> int:
    offset = context.user_data["offset"]
    with session_maker() as session:
        orders = session.query(Order).offset(offset * 5).limit(5).all()
        text = ""
        keyboard = []
        for order in orders:
            text += f"Заказ номер: {order.id}\n"
            text += f"Заказчик: {order.tg_id}"
            keyboard.append(
                [InlineKeyboardButton(f"Работать с {order.id}", callback_data=order.id)]
            )
        pages_count = session.query(Order).count() / 5
    if offset == 0:
        keyboard.append([InlineKeyboardButton(">", callback_data=">")])
    elif offset >= pages_count:
        keyboard.append([InlineKeyboardButton("<", callback_data="<")])
    elif pages_count <= 1:
        pass
    else:
        keyboard.append(
            [
                InlineKeyboardButton("<", callback_data="<"),
                InlineKeyboardButton(">", callback_data=">"),
            ]
        )
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def manage_orders_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    context.user_data["offset"] = 0
    orders_send_message(update, context)
    return states.ORDERS_ACTION


async def orders_page_swap_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    data = update.callback_query.data
    if data == "<":
        context.user_data["offset"] -= 1
    else:
        context.user_data["offset"] += 1
    await orders_send_message(update, context)


async def order_send_msg(update: Update, context: CallbackContext) -> None:
    order_id = context.user_data["current_order"]
    with session_maker() as session:
        order = session.query(Order).filter(Order.id == order_id).first()
        text = f"Заказ номер: {order.id}\n"
        text += f"Статус: {order.status}\n"
        text += f"Создан: {order.created_at}\n"
        user_data = (
            f"{order.username} {order.phone} ({order.tg_id})"
            if order.username
            else f"{order.phone} ({order.tg_id})"
        )
        text += f"Заказчик: {user_data}\n"
        text += f"Место доставки: {order.geo}\n\n"
        total_cost = 0
        for product in order.basket:
            text += f"{product[0]['name']} {product[1]} штук\n"
            total_cost += product[0]["cost"]
        text += f"\nИтоговая цена: {total_cost} руб."
        button_texts = [
            'Изменить статус на "В доставке"',
            'Изменить статус на "Доставлен"',
            'Изменить статус на "Отмена"',
        ]
        keyboard = [
            [InlineKeyboardButton(button_texts[0], callback_data="status in progress")]
        ]
        keyboard.append(
            [InlineKeyboardButton(button_texts[1], callback_data="status done")]
        )
        keyboard.append(
            [InlineKeyboardButton(button_texts[2], callback_data="status cancel")]
        )
        keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
        keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
        context.user_data[
            "msg_for_del_keys"
        ] = await update.effective_chat.send_message(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def order_action_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    data = update.callback_query.data
    context.user_data["current_order"] = data
    await order_send_msg(update, context)
    return states.ORDER_STATUS


async def order_status_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    data = update.callback_query.data
    if data == "status in progress":
        status = "В доставке"
    elif data == "status done":
        status = "Доставлен"
    elif data == "status cancel":
        status = "Отменен"
    order_id = context.user_data["current_order"]
    with session_maker() as session:
        session.query(Order).filter(Order.id == order_id).update({"status": status})
        session.commit()
    await orders_send_message(update, context)


async def back_to_orders_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    await orders_send_message(update, context)
    return states.ORDERS_ACTION


async def exit_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    await update.effective_chat.send_message(admin_messages["exit_callback_0"])
    return ConversationHandler.END


menu_handler = ConversationHandler(
    entry_points=[CommandHandler("manager", admin_entry_point)],
    states={
        states.ADMIN_ACTION: [
            CallbackQueryHandler(send_message_callback, r"send_message"),
            CallbackQueryHandler(manage_orders_callback, r"manage_orders"),
        ],
        states.SEND_MESSAGE_ASK_TEXT: [
            MessageHandler(filters.Regex(r"\d+"), send_message_callback),
        ],
        states.SEND_MESSAGE: [
            MessageHandler(filters.TEXT, send_message_callback),
        ],
        states.ORDERS_ACTION: [
            CallbackQueryHandler(orders_page_swap_callback, r"\<|\>"),
            CallbackQueryHandler(order_action_callback, r"\d+"),
        ],
        states.ORDER_STATUS: [
            CallbackQueryHandler(
                order_status_callback, r"status in progress|status done|status cancel"
            ),
            CallbackQueryHandler(back_to_orders_callback, r"back"),
        ],
    },
    fallbacks=[CallbackQueryHandler(exit_callback, r"exit")],
)
