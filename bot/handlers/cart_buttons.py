from ..bot_token import bot
from .. import db, functions, markups
from .funnel_confirmation import patient_handler


def edit_items(call):
    functions.edit_markup(call)


def delete_call(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from bot_shop.shop_clientcarts
                    where client_id = ?;""", (call.from_user.id,))
    cur.execute("""delete from bot_shop.shop_cartmeta
                    where client_id = ?;""", (call.from_user.id,))
    conn.commit()
    bot.edit_message_text(text="You cart is empty",
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)


def priority_call(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select priority from bot_shop.shop_cartmeta where client_id = ?;""", (call.from_user.id,))
    priority_status = cur.next()[0]

    if priority_status:
        cur.execute("""update bot_shop.shop_cartmeta set priority = ? where client_id = ?;""", (0, call.from_user.id))
        conn.commit()

    else:
        cur.execute("""update bot_shop.shop_cartmeta set priority = ? where client_id = ?;""", (1, call.from_user.id))
        conn.commit()

    message_text, priority_text = functions.cart_function(call)
    bot.edit_message_text(text=message_text,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          reply_markup=markups.cart_markup(priority_text))


def accept_call(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from bot_shop.shop_cartmeta where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        cur.execute("""insert into bot_shop.shop_cartmeta (client_id, patient_name, deadline, term_time, description, priority)
            values (?, ?, ?, ?, ?, ?);""", (call.from_user.id, "Patient", "2022-09-26", "18:00", "No", False))
        conn.commit()

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter full name of the patient")

    dell_msg = msg.id

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=patient_handler,
                                              dell_msg=dell_msg)


def init_bot():
    bot.register_callback_query_handler(callback=edit_items, func=lambda call: call.data == "edit")
    bot.register_callback_query_handler(callback=delete_call, func=lambda call: call.data == "delete")
    bot.register_callback_query_handler(callback=priority_call, func=lambda call: call.data == "priority")
    bot.register_callback_query_handler(callback=accept_call, func=lambda call: call.data == "confirmation")
