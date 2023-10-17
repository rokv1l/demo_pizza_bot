from datetime import datetime

from loguru import logger
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
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
from config import user_messages
from .utils import user_access_control
from src.database import session_maker, Product, Order, User
from src.telegram_utils import delete_old_keyboard, delete_old_keyboard_special


async def menu_send_msg(update: Update, context: CallbackContext, edit=False) -> None:
    products = context.user_data["products"]
    index = context.user_data["index"]
    keyboard = []
    keyboard.append(
        [
            InlineKeyboardButton("<", callback_data="<"),
            InlineKeyboardButton(">", callback_data=">"),
        ]
    )
    keyboard.append(
        [InlineKeyboardButton("Добавить в корзину", callback_data="add_to_basket")]
    )
    if len(context.user_data["basket"]) != 0:
        keyboard.append(
            [InlineKeyboardButton("Перейти в корзину", callback_data="go_to_basket")]
        )
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    text = products[index]["name"] + "\n\n"
    text += products[index]["description"] + "\n\n"
    text += f"Цена: {products[index]['cost']} руб."
    if edit:
        with open(products[index]["image"], "rb") as f:
            await update.effective_message.edit_media(
                media=InputMediaPhoto(f, caption=text),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    else:
        with open(products[index]["image"], "rb") as f:
            context.user_data[
                "msg_for_del_keys_special"
            ] = await update.effective_chat.send_photo(
                f, text, reply_markup=InlineKeyboardMarkup(keyboard)
            )


@user_access_control
async def menu_entry_point(update: Update, context: CallbackContext) -> None:
    logger.info(f"user {update.effective_chat.id} menu_entry_point")
    context.user_data["basket"] = []
    with session_maker() as session:
        product_rows = session.query(Product).all()
        products = []
        for product in product_rows:
            products.append(
                {
                    "name": product.name,
                    "description": product.description,
                    "cost": product.cost,
                    "image": product.image,
                }
            )
        context.user_data["products"] = products
        index = 0
        context.user_data["index"] = index
    await menu_send_msg(update, context)
    return states.PRODUCTS_COURUSEL


async def menu_courusel_callback(update: Update, context: CallbackContext):
    logger.info(f"user {update.effective_chat.id} menu_courusel_callback")
    data = update.callback_query.data
    products = context.user_data["products"]
    if data == "<":
        if context.user_data["index"] >= len(products) - 1:
            context.user_data["index"] = 0
        else:
            context.user_data["index"] += 1
    elif data == ">":
        if context.user_data["index"] == 0:
            context.user_data["index"] = len(products) - 1
        else:
            context.user_data["index"] -= 1
    await menu_send_msg(update, context, True)
    return states.PRODUCTS_COURUSEL


async def select_product_count_callback(update: Update, context: CallbackContext):
    logger.info(f"user {update.effective_chat.id} select_product_count_callback")
    keyboard = [[InlineKeyboardButton(i, callback_data=i) for i in range(1, 6)]]
    keyboard.append([InlineKeyboardButton("В меню", callback_data="back")])
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    products = context.user_data["products"]
    index = context.user_data["index"]
    with open(products[index]["image"], "rb") as f:
        await update.effective_message.edit_media(
            media=InputMediaPhoto(
                f, caption=user_messages["select_product_count_callback_0"]
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def add_to_basket_callback(update: Update, context: CallbackContext):
    logger.info(f"user {update.effective_chat.id} add_to_basket_callback")
    data = update.callback_query.data
    index = context.user_data["index"]
    product = context.user_data["products"][index]
    context.user_data["basket"].append([product, int(data)])
    await menu_send_msg(update, context, True)


async def go_to_basket_send_msg(update: Update, context: CallbackContext, edit=False):
    texts = []
    total_cost = 0
    for index, set_ in enumerate(context.user_data["basket"]):
        text = str(index + 1) + ") " + set_[0]["name"] + "\n"
        text += set_[0]["description"] + "\n"
        text += f"{set_[0]['cost']} руб.\n"
        text += f"Кол-во: {set_[1]}"
        texts.append(text)
        total_cost += set_[0]["cost"] * set_[1]
    texts.append(f"Итоговая цена: {total_cost}")
    text = "\n________________________________\n".join(texts)
    keyboard = [
        [InlineKeyboardButton("Изменить позицию " + str(i + 1), callback_data=i)]
        for i in range(0, len(texts) - 1)
    ]
    keyboard.append(
        [InlineKeyboardButton("Оформить заказ", callback_data="make_order")]
    )
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    if edit:
        await update.effective_message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def go_to_basket_callback(update: Update, context: CallbackContext):
    logger.info(f"user {update.effective_chat.id} go_to_basket_callback")
    await delete_old_keyboard_special(context, update.effective_chat.id)
    await go_to_basket_send_msg(update, context)
    return states.BASKET_ACTION


async def change_basket_position_send_msg(
    update: Update, context: CallbackContext, edit=False
) -> None:
    logger.info(f"user {update.effective_chat.id} change_basket_position_send_msg")
    position = context.user_data["change_position"]
    keyboard = [
        [
            InlineKeyboardButton("-1", callback_data="-1"),
            InlineKeyboardButton("+1", callback_data="+1"),
        ]
    ]
    if len(context.user_data["basket"]) > 1:
        keyboard.append(
            [InlineKeyboardButton("Удалить позицию", callback_data="delete_position")]
        )
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
    keyboard.append([InlineKeyboardButton("Выход", callback_data="exit")])
    text = context.user_data["basket"][position][0]["name"] + "\n"
    text += f"Кол-во: {context.user_data['basket'][position][1]}"
    if edit:
        await update.effective_message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def change_basket_position_callback(
    update: Update, context: CallbackContext
) -> None:
    logger.info(f"user {update.effective_chat.id} change_basket_position_callback")
    context.user_data["change_position"] = int(update.callback_query.data)
    await change_basket_position_send_msg(update, context, edit=True)


async def change_position_count_callback(
    update: Update, context: CallbackContext
) -> int:
    logger.info(f"user {update.effective_chat.id} change_position_count_callback")
    position = context.user_data["change_position"]
    data = update.callback_query.data
    if data == "-1":
        context.user_data["basket"][position][1] -= 1
    elif data == "+1":
        context.user_data["basket"][position][1] += 1
    return await change_basket_position_send_msg(update, context, edit=True)


async def delete_basket_position_callback(
    update: Update, context: CallbackContext
) -> int:
    logger.info(f"user {update.effective_chat.id} delete_basket_position_callback")
    position = context.user_data["change_position"]
    context.user_data["basket"].pop(position)
    await go_to_basket_send_msg(update, context, edit=True)
    return states.BASKET_ACTION


async def make_order_ask_geo_callback(update: Update, context: CallbackContext) -> int:
    logger.info(f"user {update.effective_chat.id} make_order_ask_geo_callback")
    await delete_old_keyboard(context, update.effective_chat.id)
    keyboard = [[KeyboardButton("Отправить геолокацию", request_location=True)]]
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        user_messages["make_order_ask_geo_callback_0"],
        reply_markup=ReplyKeyboardMarkup(keyboard),
    )
    return states.MAKE_ORDER


async def back_to_basket_callback(update: Update, context: CallbackContext) -> int:
    logger.info(f"user {update.effective_chat.id} back_to_basket_callback")
    await go_to_basket_send_msg(update, context, edit=True)
    return states.BASKET_ACTION


async def make_order_callback(update: Update, context: CallbackContext) -> None:
    logger.info(f"user {update.effective_chat.id} make_order_callback")
    await delete_old_keyboard(context, update.effective_chat.id)
    geodata_ = update.message.location.to_dict()
    with session_maker() as session:
        user = (
            session.query(User).filter(User.tg_id == update.effective_chat.id).first()
        )
        order_ = Order(
            tg_id=update.effective_chat.id,
            username=update.effective_chat.username,
            basket=context.user_data["basket"],
            geo=geodata_,
            phone=user.phone,
            created_at=datetime.now(),
        )
        session.add(order_)
        session.commit()
    await update.effective_chat.send_message(user_messages["make_order_callback_0"])
    return ConversationHandler.END


async def back_callback(update: Update, context: CallbackContext) -> None:
    logger.info(f"user {update.effective_chat.id} back_callback")
    if context.user_data.get("msg_for_del_keys"):
        await menu_send_msg(update, context, True)
    else:
        await delete_old_keyboard(context, update.effective_chat.id)
        await delete_old_keyboard_special(context, update.effective_chat.id)
        await menu_send_msg(update, context)
    return states.PRODUCTS_COURUSEL


async def exit_callback(update: Update, context: CallbackContext) -> None:
    logger.info(f"user {update.effective_chat.id} exit_callback")
    await delete_old_keyboard(context, update.effective_chat.id)
    await delete_old_keyboard_special(context, update.effective_chat.id)
    await update.effective_chat.send_message(user_messages["exit_callback_0"])
    return ConversationHandler.END


menu_handler = ConversationHandler(
    entry_points=[CommandHandler("menu", menu_entry_point)],
    states={
        states.PRODUCTS_COURUSEL: [
            CallbackQueryHandler(menu_courusel_callback, r"\<|\>"),
            CallbackQueryHandler(select_product_count_callback, r"add_to_basket"),
            CallbackQueryHandler(go_to_basket_callback, r"go_to_basket"),
            CallbackQueryHandler(add_to_basket_callback, r"\d"),
        ],
        states.BASKET_ACTION: [
            CallbackQueryHandler(change_basket_position_callback, r"\d+"),
            CallbackQueryHandler(change_position_count_callback, r"\-1|\+1"),
            CallbackQueryHandler(delete_basket_position_callback, r"delete_position"),
            CallbackQueryHandler(make_order_ask_geo_callback, r"make_order"),
            CallbackQueryHandler(back_to_basket_callback, r"back"),
        ],
        states.MAKE_ORDER: [
            MessageHandler(filters.LOCATION, make_order_callback),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_callback, r"back"),
        CallbackQueryHandler(exit_callback, r"exit"),
    ],
)
