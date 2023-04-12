from ..bot_token import bot
from .. import db, functions, markups
from mariadb import OperationalError
from telebot.apihelper import ApiTelegramException


def edit_items(call):
    """
    Allows user to see info about each item in cart and chage it
    """
    functions.edit_cart_buttons(call)


def empty_cart(call):
    """
    Removing items from the cart and removing an order from the temporary table
    """
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from  shop_clientcarts
                    where client_id = ?;""", (call.from_user.id,))
    cur.execute("""delete from  shop_cartmeta
                    where client_id = ?;""", (call.from_user.id,))
    conn.commit()
    bot.edit_message_text(text="You cart is empty",
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)


def set_priority(call):
    """
    Sets/removes order's priority
    """

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select priority from  shop_cartmeta where client_id = ?;""", (call.from_user.id,))
    priority_status = cur.next()[0]

    if priority_status:
        cur.execute("""update  shop_cartmeta set priority = ? where client_id = ?;""", (0, call.from_user.id))
        conn.commit()

    else:
        cur.execute("""update  shop_cartmeta set priority = ? where client_id = ?;""", (1, call.from_user.id))
        conn.commit()

    message_text, priority_text = functions.items_in_cart(call)
    bot.edit_message_text(text=message_text,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          reply_markup=markups.cart_markup(priority_text))


def confirm_order(call):
    """
    Creates an order in temporary table
    Starts funnel of order's confirmatiion
    """

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from shop_cartmeta where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        cur.execute("""insert into shop_cartmeta (client_id, patient_name, deadline, term_time, description, priority)
            values (?, ?, ?, ?, ?, ?);""", (call.from_user.id, "Patient", "2022-09-26", "18:00", "No", False))
        conn.commit()

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter full name of the patient")

    dell_msg = msg.id

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=patient_handler,
                                              dell_msg=dell_msg)


def patient_handler(call, dell_msg):
    """
    Responds to sharing name, updates it and activates the next confirmation step - getting a date
    """

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update  shop_cartmeta set patient_name = ? where client_id = ?;""", (call.text, call.from_user.id))
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
    """
    Responds to sharing date, updates it and activates the next confirmation step - getting a time
    """

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update  shop_cartmeta set deadline = ? where client_id = ?;""", (call.text, call.from_user.id))
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
    """
    Responds to sharing time, updates it and activates the last confirmation step - getting a description
    """

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update  shop_cartmeta set term_time = ? where client_id = ?;""", (call.text, call.from_user.id))
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
