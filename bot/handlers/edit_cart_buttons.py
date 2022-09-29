from ..bot_token import bot
from .. import db, functions, markups
from telebot.apihelper import ApiTelegramException


def select_item(call):

    row_id = int(call.data.split()[1])
    functions.edit_item_in_cart(call=call, row_id=row_id)


def back_to_catalogue(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text="You can choose our goods",
                          reply_markup=markups.catalogue_markup())


def minus_item(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""delete from bot_shop.shop_clientcarts
                        where client_id = ? and product_id = ?
                        limit 1;""", (call.from_user.id, item_id,))

        conn.commit()

        try:
            functions.edit_item_in_cart(call=call, row_id=row_id)

        except TypeError:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=call.message.id,
                                  text="Your cart is empty")

    except ApiTelegramException:
        pass


def item_quantity(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter quantity")
    edit_msg = msg.id
    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=quantity_handler,
                                              edit_msg=edit_msg,
                                              item_id=item_id,
                                              row_id=row_id,
                                              cart_call=call)


def quantity_handler(call, edit_msg, item_id, row_id, cart_call):

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
                                                  callback=quantity_handler,
                                                  edit_msg=edit_msg,
                                                  item_id=item_id,
                                                  row_id=row_id,
                                                  cart_call=cart_call)
        return

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from bot_shop.shop_clientcarts where client_id = ? and product_id = ?;""",
                (call.from_user.id, item_id))

    while quantity != 0:
        quantity -= 1
        cur.execute("""insert into bot_shop.shop_clientcarts (client_id, product_id) values (?, ?);""",
                    (call.from_user.id, item_id))

    conn.commit()

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=edit_msg,
                          text="Nice")

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)
    try:
        functions.edit_item_in_cart(call=cart_call, row_id=row_id)

    except ApiTelegramException:
        pass


def plus_item(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""insert into bot_shop.shop_clientcarts (client_id, product_id)
                        values (?, ?);""", (call.from_user.id, item_id,))

        conn.commit()

        functions.edit_item_in_cart(call=call, row_id=row_id)

    except ApiTelegramException:
        pass


def previous_item(call):

    row_id = int(call.data.split()[1]) - 1
    functions.edit_cart_buttons(call=call, row_id=row_id)


def next_item(call):

    row_id = int(call.data.split()[1]) + 1
    functions.edit_cart_buttons(call=call, row_id=row_id)


def back_to_cart(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from bot_shop.shop_clientcarts where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=call.from_user.id,
                                text="You bin is empty")

    message_text, priority_text = functions.items_in_cart(call)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=message_text,
                          reply_markup=markups.cart_markup(priority_text))


def init_bot():
    bot.register_callback_query_handler(callback=select_item, func=lambda call: call.data.startswith("item"))
    bot.register_callback_query_handler(callback=minus_item, func=lambda call: call.data.startswith("minus"))
    bot.register_callback_query_handler(callback=item_quantity, func=lambda call: call.data.startswith("rewrite"))
    bot.register_callback_query_handler(callback=plus_item, func=lambda call: call.data.startswith("plus"))
    bot.register_callback_query_handler(callback=back_to_catalogue, func=lambda call: call.data == "continue")
    bot.register_callback_query_handler(callback=next_item, func=lambda call: call.data.startswith("forward"))
    bot.register_callback_query_handler(callback=previous_item, func=lambda call: call.data.startswith("reaward"))
    bot.register_callback_query_handler(callback=back_to_cart, func=lambda call: call.data == "finish")
