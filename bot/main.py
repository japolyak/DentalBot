import telebot
import db
from telebot import types
import functions
from config import token

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM polls_clients WHERE client_id = ?;", (user_id,))
    check = cur.next()

    if check is None:
        cur.execute("INSERT INTO polls_clients (client_id) VALUES (?);", (user_id,))
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_button = types.KeyboardButton("Phone number", request_contact=True, )
        markup.add(phone_button)
        bot.send_message(message.chat.id,
                         "You are not in DB\nEnter your number by pushing button below",
                         reply_markup=markup)
    else:
        functions.welcome_word(message)


@bot.message_handler(content_types=['contact'])
def check_phone(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""UPDATE polls_clients
                    SET
                        client_number = ?
                    WHERE
                        client_id = ?;""", (("+" + message.contact.phone_number), message.from_user.id))
    conn.commit()

    msg = bot.send_message(message.chat.id,
                           "Enter your dental name",
                           reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, name_handler)


def name_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""UPDATE polls_clients
                    SET
                        client_name = ?
                    WHERE
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()

    msg = bot.send_message(message.chat.id,
                           "Enter your address",
                           reply_markup=telebot.types.ReplyKeyboardRemove(selective=False))
    bot.register_next_step_handler(msg, address_handler)


# Почему она неотделима?!
def address_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""UPDATE polls_clients
                    SET
                        client_address = ?
                    WHERE
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()
    functions.welcome_word(message)


@bot.message_handler(regexp="Товари")
def category(message):
    bot.send_message(message.chat.id, "Привет! Я помогу подобрать товар!", reply_markup=functions.keyboard('start'))


@bot.message_handler(regexp="Cart")
def buttons_handler(message):

    message_text, priority_text = functions.cart_function(message)

    bot.send_message(chat_id=message.from_user.id,
                     text=message_text,
                     reply_markup=functions.cart_markup(priority_text))


@bot.message_handler(regexp="Замовлення")
def order_handler(message):
    bot.send_message(message.chat.id, "Here will be inforamtion about your orders.")


@bot.message_handler(regexp="Інфо")
def info_handler(message):
    bot.send_message(message.chat.id, "Bla bla bla.")


@bot.callback_query_handler(func=lambda call: True)  # дублирует принт почему-то
def buttons_call(call):
    action = call.data.split()[0]
    item_id = call.data.split()[1]
    user = call.from_user.id

    if action == "back":
        bot.edit_message_text(text="Привет! Я помогу подобрать товар!",
                              inline_message_id=call.inline_message_id,
                              reply_markup=functions.keyboard('start'))
    conn = db.get_db()
    cur = conn.cursor()

    if action == "+1":
        cur.execute("""INSERT INTO polls_clientcarts (client_id, product_id)
                        VALUES (?, ?);""", (user, item_id,))
        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=functions.item_keyboard(user, item_id))

    elif action == "clean":
        cur.execute("""DELETE FROM polls_clientcarts
                        WHERE client_id = ? AND product_id = ?;""", (user, item_id,))
        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=functions.item_keyboard(user, item_id))

    elif action == "-1":
        cur.execute("""DELETE FROM polls_clientcarts
                        WHERE client_id = ? AND product_id = ?
                        LIMIT 1;""", (user, item_id,))

        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=functions.item_keyboard(user, item_id))

    elif action == "cart":
        message_text, priority_text = functions.cart_function(call)

        bot.send_message(chat_id=call.from_user.id,
                         text=message_text,
                         reply_markup=functions.cart_markup(priority_text))

    elif action == "priority":
        cur.execute("""select priority from polls_cart_meta where client_id = ?;""", (user, ))
        priority_status = cur.next()[0]

        if priority_status:
            cur.execute("""update polls_cart_meta set priority = ? where client_id = ?;""", (0, user))
            conn.commit()

        else:
            cur.execute("""update polls_cart_meta set priority = ? where client_id = ?;""", (1, user))
            conn.commit()

        message_text, priority_text = functions.cart_function(call)
        bot.edit_message_text(text=message_text,
                              message_id=call.message.message_id,
                              chat_id=call.message.chat.id,
                              reply_markup=functions.cart_markup(priority_text))


@bot.inline_handler(func=lambda query: len(query.query) > 0)
def inline_query(query):
    category = query.query
    conn = db.get_db()
    cur = conn.cursor()

    inline_id = 1
    inline_items = []

    cur.execute("""select id, product_name, price  from polls_products where category = ?;""", (category,))

    while True:
        inline_info = cur.next()
        if not inline_info:
            break
        but = types.InlineQueryResultArticle(
            id=f"{inline_id}", title=inline_info[1], description=f"₴ {inline_info[2]}",
            input_message_content=types.InputTextMessageContent(message_text=inline_info[1]),
            reply_markup=functions.item_keyboard(query.from_user.id, inline_info[0])
        )
        inline_items.append(but)
        inline_id += 1

    bot.answer_inline_query(query.id, inline_items)


# @bot.callback_query_handler(func=lambda call: True)
# def callback_inline(call):
#     sub_category = call.data
#     print(call)
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
#                           text=sub_category, reply_markup=keyboard(sub_category))
# bot.answer_inline_query()
# if call.data == 'Ceramet':
#     bot.send_message(chat_id=call.message.chat.id, text='hello')
#     # bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
#     #                       text='подкатегория', reply_markup=keyboard('subcategory'))
# elif call.data == '2_1_inline':
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
#                           text='товар', reply_markup=keyboard('product'))
# elif call.data == '3_1_inline':
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
#                           text='Описание товара')
#     bot.send_photo(call.message.chat.id,
#                    'https://cs13.pikabu.ru/images/big_size_comm/2020-06_3/159194100716237333.jpg')


if __name__ == '__main__':
    bot.polling(none_stop=True)
