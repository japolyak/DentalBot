from ..bot_token import bot
from .. import db, markups
from telebot.apihelper import ApiTelegramException
from mariadb import OperationalError


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
                     reply_markup=markups.yes_no())
