from ..bot_token import bot
from .. import db, functions, markups
from mariadb import OperationalError
from telebot.apihelper import ApiTelegramException


def edit_items(call):
    functions.edit_cart_buttons(call)


def empty_cart(call):

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


def set_priority(call):

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

    message_text, priority_text = functions.items_in_cart(call)
    bot.edit_message_text(text=message_text,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          reply_markup=markups.cart_markup(priority_text))


def confirm_order(call):

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


def patient_handler(call, dell_msg):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update bot_shop.shop_cartmeta set patient_name = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=dell_msg)

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter the date")

    edit_msg = msg.id

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=deadline_handler,
                                              edit_msg=edit_msg)


def deadline_handler(call, edit_msg):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update bot_shop.shop_cartmeta set deadline = ? where client_id = ?;""", (call.text, call.from_user.id))
        conn.commit()

    except OperationalError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)
        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="Enter date like this - yyyy-mm-dd")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=deadline_handler,
                                                  edit_msg=edit_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter the time")

    edit_msg = msg.id

    bot.register_next_step_handler(message=msg,
                                   callback=term_time_handler,
                                   edit_msg=edit_msg)


def term_time_handler(call, edit_msg):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update bot_shop.shop_cartmeta set term_time = ? where client_id = ?;""", (call.text, call.from_user.id))
        conn.commit()

    except OperationalError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)
        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="Enter time like this - hh:mm")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=term_time_handler,
                                                  edit_msg=edit_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)

    bot.send_message(chat_id=call.from_user.id,
                     text="Leave description?",
                     reply_markup=markups.leave_description_markup())


def init_bot():
    bot.register_callback_query_handler(callback=edit_items, func=lambda call: call.data == "edit")
    bot.register_callback_query_handler(callback=empty_cart, func=lambda call: call.data == "delete")
    bot.register_callback_query_handler(callback=set_priority, func=lambda call: call.data == "priority")
    bot.register_callback_query_handler(callback=confirm_order, func=lambda call: call.data == "confirmation")
