from ..bot_token import bot
from .. import db, functions, markups
from telebot.apihelper import ApiTelegramException
from mariadb import OperationalError


def edit_fullname(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new fullname of the patient")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=functions.new_fullname_or_description,
                                              back_msg=back_msg.message_id,
                                              field=call.data)


def edit_day(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new term")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=new_term,
                                              back_msg=back_msg.message_id)


def new_term(call, back_msg):

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
                                  message_id=back_msg,
                                  text="Enter date like this - yyyy-mm-dd")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=new_term,
                                                  back_msg=back_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=back_msg,
                          text=functions.order_details(call),
                          reply_markup=markups.order_confirmation_markup())


def edit_time(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new time")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=new_time,
                                              back_msg=back_msg.message_id)


def new_time(call, back_msg):

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
                                  message_id=back_msg,
                                  text="Enter time like this - hh:mm")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=new_time,
                                                  back_msg=back_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=back_msg,
                          text=functions.order_details(call),
                          reply_markup=markups.order_confirmation_markup())


def edit_description(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new description")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=functions.new_fullname_or_description,
                                              back_msg=back_msg.message_id,
                                              field=call.data)


def edit_tech_info(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=functions.order_details(call),
                          reply_markup=markups.order_confirmation_markup())


def init_bot():
    bot.register_callback_query_handler(callback=edit_fullname, func=lambda call: call.data == "fullname")
    bot.register_callback_query_handler(callback=edit_day, func=lambda call: call.data == "day")
    bot.register_callback_query_handler(callback=edit_time, func=lambda call: call.data == "time")
    bot.register_callback_query_handler(callback=edit_description, func=lambda call: call.data == "description")
    bot.register_callback_query_handler(callback=edit_tech_info, func=lambda call: call.data == "return")
