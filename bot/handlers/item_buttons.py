from ..bot_token import bot
from .. import db, functions, markups
from telebot.apihelper import ApiTelegramException


def minus_item(call):

    item_id = call.data.split()[1]

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""delete from bot_shop.shop_clientcarts
                        where client_id = ? and product_id = ?
                        limit 1;""", (call.from_user.id, item_id,))

        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=markups.item_keyboard(call.from_user.id, item_id))
    except ApiTelegramException:
        pass


def item_quantity(call):

    item_id = call.data.split()[1]

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter quantity")
    edit_msg = msg.id
    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=entered_quantity,
                                              edit_msg=edit_msg,
                                              item_id=item_id,
                                              edit_markup=call.inline_message_id)


def entered_quantity(call, edit_msg, item_id, edit_markup):

    try:
        quantity = int(call.text)

    except ValueError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)

        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="You should enter numbers")

        except ApiTelegramException:
            pass

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=entered_quantity,
                                                  edit_msg=edit_msg,
                                                  item_id=item_id,
                                                  edit_markup=edit_markup)
        return

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from bot_shop.shop_clientcarts where client_id = ? and product_id = ?;""", (call.from_user.id, item_id))

    while quantity != 0:
        quantity -= 1
        cur.execute("""insert into bot_shop.shop_clientcarts (client_id, product_id) values (?, ?);""", (call.from_user.id, item_id))

    conn.commit()

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=edit_msg,
                          text="Nice")

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)

    try:
        bot.edit_message_reply_markup(inline_message_id=edit_markup,
                                      reply_markup=markups.item_keyboard(call.from_user.id, item_id))
    except ApiTelegramException:
        pass


def plus_item(call):

    item_id = call.data.split()[1]

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""insert into bot_shop.shop_clientcarts (client_id, product_id)
                    values (?, ?);""", (call.from_user.id, item_id,))
    conn.commit()

    try:
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=markups.item_keyboard(call.from_user.id, item_id))
    except ApiTelegramException:
        pass


def delete_item(call):

    item_id = call.data.split()[1]

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""delete from bot_shop.shop_clientcarts
                        where client_id = ? and product_id = ?;""", (call.from_user.id, item_id,))
        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=markups.item_keyboard(call.from_user.id, item_id))
    except ApiTelegramException:
        pass


def show_cart(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from bot_shop.shop_clientcarts where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=call.from_user.id,
                                text="You cart is empty")

    message_text, priority_text = functions.items_in_cart(call)

    bot.send_message(chat_id=call.from_user.id,
                     text=message_text,
                     reply_markup=markups.cart_markup(priority_text))


def back_to_catalogue(call):

    bot.edit_message_text(text="Hi, You can choose one of our goods!",
                          inline_message_id=call.inline_message_id,
                          reply_markup=markups.catalogue_markup())


def init_bot():
    bot.register_callback_query_handler(callback=minus_item, func=lambda call: call.data.startswith("-1"))
    bot.register_callback_query_handler(callback=item_quantity, func=lambda call: call.data.startswith("quantity"))
    bot.register_callback_query_handler(callback=plus_item, func=lambda call: call.data.startswith("+1"))
    bot.register_callback_query_handler(callback=delete_item, func=lambda call: call.data.startswith("clear"))
    bot.register_callback_query_handler(callback=show_cart, func=lambda call: call.data == "cart")
    bot.register_callback_query_handler(callback=back_to_catalogue, func=lambda call: call.data == "back")
