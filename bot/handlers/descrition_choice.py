from ..bot_token import bot
from .. import functions, markups


def yes_call(call):

    msg = bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.id,
                                text="Enter description")

    bot.register_next_step_handler(message=msg,
                                   callback=functions.description_handler)


def show_order_call(call):

    text = functions.confirmation_text(call)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=text,
                          reply_markup=markups.confirmation_markup())


def init_bot():
    bot.register_callback_query_handler(callback=yes_call, func=lambda call: call.data == "yes")
    bot.register_callback_query_handler(callback=show_order_call, func=lambda call: call.data == "no")
