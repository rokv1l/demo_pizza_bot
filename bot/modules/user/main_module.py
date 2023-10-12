
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters

from .utils import user_access_control


@user_access_control
async def menu_fill_order_controller(update: Update, context: CallbackContext):
    pass


menu_handler = ConversationHandler(
    entry_points=[CommandHandler("menu", menu_fill_order_controller)],
    states={
    },
    fallbacks=[]
)
