from ..bot_token import bot
from .. import db, functions, markups


def confirm_order(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=functions.information_about_order(call))


def edit_details(call):

    bot.edit_message_text(text="Choose what do you whant to change",
                          chat_id=call.from_user.id,
                          message_id=call.message.id,
                          reply_markup=markups.edit_details_markup())


def cancel_order(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from  shop_cartmeta where client_id = ?;""", (call.from_user.id, ))
    cur.execute("""delete from  shop_clientcarts where client_id = ?;""", (call.from_user.id,))
    conn.commit()

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text="Your order was canceled")


def init_bot():
    bot.register_callback_query_handler(callback=confirm_order, func=lambda call: call.data == "accept")
    bot.register_callback_query_handler(callback=edit_details, func=lambda call: call.data == "correct")
    bot.register_callback_query_handler(callback=cancel_order, func=lambda call: call.data == "cancel")
