from ..bot_token import bot
from .. import functions, markups


def add_description(call):

    msg = bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.id,
                                text="Enter description")

    bot.register_next_step_handler(message=msg,
                                   callback=functions.add_description)


def show_order(call):

    text = functions.order_details(call)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=text,
                          reply_markup=markups.order_confirmation_markup())


def init_bot():
    bot.register_callback_query_handler(callback=add_description, func=lambda call: call.data == "yes")
    bot.register_callback_query_handler(callback=show_order, func=lambda call: call.data == "no")
