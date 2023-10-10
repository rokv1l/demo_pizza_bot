
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters


def ask_contact_send_msg(update: Update, context: CallbackContext) -> int:
    # Отправьте контакт
    pass


def menu_fill_order_controller(update: Update, context: CallbackContext):
    pass


menu_handler = ConversationHandler(
    entry_points=[CommandHandler("menu", menu_fill_order_controller)],
    states={
    },
    fallbacks=[]
)
