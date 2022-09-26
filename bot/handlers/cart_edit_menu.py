from ..bot_token import bot
from .. import db, functions, markups
from telebot.apihelper import ApiTelegramException


def select_item(call):

    row_id = int(call.data.split()[1])
    functions.cart_edit_markup(call=call, row_id=row_id)


def editable_minus(call):

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
            functions.cart_edit_markup(call=call, row_id=row_id)

        except TypeError:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=call.message.id,
                                  text="Your cart is empty")

    except ApiTelegramException:
        pass


def rewrite_quantity(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter quantity")
    edit_msg = msg.id
    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=next_rewrite_quantity,
                                              edit_msg=edit_msg,
                                              item_id=item_id,
                                              row_id=row_id,
                                              cart_call=call)


def next_rewrite_quantity(call, edit_msg, item_id, row_id, cart_call):

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
                                                  callback=next_rewrite_quantity,
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
        functions.cart_edit_markup(call=cart_call, row_id=row_id)

    except ApiTelegramException:
        pass


def editable_plus(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""insert into bot_shop.shop_clientcarts (client_id, product_id)
                        values (?, ?);""", (call.from_user.id, item_id,))

        conn.commit()

        functions.cart_edit_markup(call=call, row_id=row_id)

    except ApiTelegramException:
        pass


def back_to_goods(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text="You can choose our goods",
                          reply_markup=markups.keyboard('start'))


def edit_forw_items(call):

    row_id = int(call.data.split()[1]) + 1
    functions.edit_markup(call=call, row_id=row_id)


def edit_reaw_items(call):

    row_id = int(call.data.split()[1]) - 1
    functions.edit_markup(call=call, row_id=row_id)


def close_editing(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from bot_shop.shop_clientcarts where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=call.from_user.id,
                                text="You bin is empty")

    message_text, priority_text = functions.cart_function(call)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=message_text,
                          reply_markup=markups.cart_markup(priority_text))


def init_bot():
    bot.register_callback_query_handler(callback=select_item, func=lambda call: call.data.startswith("item"))
    bot.register_callback_query_handler(callback=editable_minus, func=lambda call: call.data.startswith("minus"))
    bot.register_callback_query_handler(callback=rewrite_quantity, func=lambda call: call.data.startswith("rewrite"))
    bot.register_callback_query_handler(callback=editable_plus, func=lambda call: call.data.startswith("plus"))
    bot.register_callback_query_handler(callback=back_to_goods, func=lambda call: call.data == "continue")
    bot.register_callback_query_handler(callback=edit_forw_items, func=lambda call: call.data.startswith("forward"))
    bot.register_callback_query_handler(callback=edit_reaw_items, func=lambda call: call.data.startswith("reaward"))
    bot.register_callback_query_handler(callback=close_editing, func=lambda call: call.data == "finish")
