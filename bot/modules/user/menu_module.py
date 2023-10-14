from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
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
from src.telegram_utils import delete_old_keyboard


async def menu_send_msg(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
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
    keyboard.append(
        [InlineKeyboardButton("Перейти в корзину", callback_data="go_to_basket")]
    )
    keyboard += [InlineKeyboardButton("Выход", callback_data="exit")]
    text = products[index]["name"] + "\n\n"
    text += products[index]["description"] + "\n\n"
    text += f"Цена: {products[index]['cost']} руб."
    with open(products[index]["img"], "rb") as f:
        context.user_data["msg_for_del_keys"] = await update.effective_chat.send_photo(
            f, text, reply_markup=InlineKeyboardMarkup(keyboard)
        )


@user_access_control
async def menu_entry_point(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
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
    await delete_old_keyboard(context, update.effective_chat.id)
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
    await menu_send_msg(update, context)
    return states.PRODUCTS_COURUSEL


async def select_product_count_callback(update: Update, context: CallbackContext):
    await delete_old_keyboard(context, update.effective_chat.id)
    keyboard = [[InlineKeyboardButton(i, callback_data=i) for i in range(1, 6)]]
    keyboard.append([InlineKeyboardButton("В меню", callback_data="back")])
    keyboard += [InlineKeyboardButton("Выход", callback_data="exit")]
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        user_messages["select_product_count_callback_0"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def add_to_basket_callback(update: Update, context: CallbackContext):
    await delete_old_keyboard(context, update.effective_chat.id)
    data = update.callback_query.data
    index = context.user_data["index"]
    product = context.user_data["products"][index]
    context.user_data["basket"].append((product, data))
    await update.effective_chat.send_message(
        user_messages["add_to_basket_callback_0"].format(product["name"], data)
    )
    await menu_send_msg(update, context)


async def go_to_basket_callback(update: Update, context: CallbackContext):
    await delete_old_keyboard(context, update.effective_chat.id)
    texts = []
    total_cost = 0
    for index, set_ in enumerate(context.user_data["products"]):
        text = str(index) + ") " + set_[0]["name"] + "\n"
        text += set_[0]["description"] + "\n"
        text += f"{set_[0]['cost']} руб.\n"
        text += "Кол-во: " + set_[1]
        texts.append(text)
        total_cost += set_[0]["cost"]
    texts.append(f"Итоговая цена: {total_cost}")
    text = "\n________________________________\n".join(texts)
    keyboard = [
        [InlineKeyboardButton("Изменить позицию " + str(i), callback_data=i)]
        for i in range(0, len(texts))
    ]
    keyboard += [InlineKeyboardButton("Оформить заказ", callback_data="make_order")]
    keyboard += [InlineKeyboardButton("Выход", callback_data="exit")]
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return states.BASKET_ACTION


async def change_basket_position_send_msg(
    update: Update, context: CallbackContext
) -> None:
    position = context.user_data["change_position"]
    keyboard = [
        [
            InlineKeyboardButton("-1", callback_data="-1"),
            InlineKeyboardButton("+1", callback_data="+1"),
        ]
    ]
    keyboard += [
        InlineKeyboardButton("Удалить позицию", callback_data="delete_position")
    ]
    keyboard += [InlineKeyboardButton("Назад", callback_data="back")]
    keyboard += [InlineKeyboardButton("Выход", callback_data="exit")]
    text = context.user_data["products"][position][0]["name"] + "\n"
    text += "Кол-во: " + context.user_data["products"][position][1]
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def change_basket_position_callback(
    update: Update, context: CallbackContext
) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    context.user_data["change_position"] = int(update.callback_query.data)
    await change_basket_position_send_msg(update, context)


async def change_position_count_callback(
    update: Update, context: CallbackContext
) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    position = context.user_data["change_position"]
    data = update.callback_query.data
    if data == "-1":
        context.user_data["products"][position][1] -= 1
    elif data == "+1":
        context.user_data["products"][position][1] += 1
    return await change_basket_position_send_msg(update, context)


async def delete_basket_position_callback(
    update: Update, context: CallbackContext
) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    position = context.user_data["change_position"]
    context.user_data["products"].pop(position)
    return await change_basket_position_send_msg(update, context)


async def make_order_ask_geo_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    keyboard = KeyboardButton("Отправить геолокацию", request_location=True)
    keyboard += [InlineKeyboardButton("Выход", callback_data="exit")]
    context.user_data["msg_for_del_keys"] = await update.effective_chat.send_message(
        user_messages["make_order_ask_geo_callback_0"],
        reply_markup=ReplyKeyboardMarkup(keyboard),
    )
    return states.MAKE_ORDER


async def back_to_basket_callback(update: Update, context: CallbackContext) -> int:
    await delete_old_keyboard(context, update.effective_chat.id)
    await go_to_basket_callback(update, context)


async def make_order_callback(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
    geodata_ = update.message.location
    with session_maker() as session:
        user = (
            session.query(User).filter(User.tg_id == update.effective_chat.id).first()
        )
        order_ = Order(
            tg_id=update.effective_chat.id,
            username=update.effective_chat.username,
            basket=context.user_data["products"],
            geo=geodata_,
            phone=user.phone,
            created_at=datetime.now(),
        )
        session.add(order_)
        session.commit()
    await update.effective_chat.send_message(user_messages["make_order_callback_0"])
    return ConversationHandler.END


async def exit_callback(update: Update, context: CallbackContext) -> None:
    await delete_old_keyboard(context, update.effective_chat.id)
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
        CallbackQueryHandler(menu_send_msg, r"back"),
        CallbackQueryHandler(exit_callback, r"exit"),
    ],
)
