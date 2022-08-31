import telebot
import db
from telebot import types
from config import token

bot = telebot.TeleBot(token)


def welcome_word(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    position_button = types.KeyboardButton("Товари")
    basket_button = types.KeyboardButton("Кошик")
    profile_button = types.KeyboardButton("Профіль")
    info_button = types.KeyboardButton("Інфо")

    markup.add(position_button,
               basket_button,
               profile_button,
               info_button)

    bot.send_message(message.chat.id, "Welcome to the club, buddy!", reply_markup=markup)


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
        welcome_word(message)


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


def address_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""UPDATE polls_clients
                    SET
                        client_address = ?
                    WHERE
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()

    welcome_word(message)


# @bot.message_handler(regexp="Товари")
# def buttons_handler(message):
#     markup = types.InlineKeyboardMarkup()
#     markup.add(types.InlineKeyboardButton("First"),
#                types.InlineKeyboardButton("Second"),
#                types.InlineKeyboardButton("Third"),
#                types.InlineKeyboardButton("Fourth"))
#
#     bot.send_message(message.chat.id, "Choose type of work!", reply_markup=markup)


@bot.message_handler(regexp="Товари")
def category(message):
    bot.send_message(message.chat.id, "Привет! Я помогу подобрать товар!", reply_markup=keyboard('start'))


@bot.message_handler(regexp="Кошик")
def buttons_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""SELECT *
                    FROM polls_clientcarts
                    WHERE client_id = ?;""", (message.from_user.id,))

    while True:
        row = cur.next()
        if not row:
            bot.send_message(message.chat.id, "You bin is empty")
            break
        print(row)

    bot.send_message(message.chat.id, "Here will be inforamtion about your order")


@bot.message_handler(regexp="Замовлення")
def buttons_handler(message):
    bot.send_message(message.chat.id, "Here will be inforamtion about your orders.")


@bot.message_handler(regexp="Інфо")
def buttons_handler(message):
    bot.send_message(message.chat.id, "Bla bla bla.")


def keyboard(call):
    if call == "start":
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""select distinct category from polls_products;""")
        list_of_goods = []

        while True:
            category_item = cur.next()
            if not category_item:
                break
            list_of_goods.append(category_item[0])

        buttons = []

        for good in list_of_goods:
            # buttons.append(types.InlineKeyboardButton(text=good, callback_data=good))
            buttons.append(types.InlineKeyboardButton(text=good,
                                                      switch_inline_query_current_chat=good))

        markup = types.InlineKeyboardMarkup(buttons_menu(buttons, n_cols=1))
        return markup


def buttons_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def item_keyboard(person_id, item_id):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""SELECT COUNT(*)
                    FROM polls_clientcarts
                    where client_id = ? and product_id = ?;""", (person_id, item_id))
    item_quantity = cur.next()
    # print(item_quantity) выполняется столько раз, сколько элементов категории

    markup = types.InlineKeyboardMarkup()

    minus_one = types.InlineKeyboardButton(text='-1', callback_data=f'-1 {item_id}')
    orders = types.InlineKeyboardButton(text=f'{item_quantity[0]} pcs', callback_data=f'quantity {item_id}')
    plus_one = types.InlineKeyboardButton(text='+1', callback_data=f'+1 {item_id}')
    clear = types.InlineKeyboardButton(text='Clear', callback_data=f'clear {item_id}')
    cart = types.InlineKeyboardButton(text='Cart', callback_data=f'cart {item_id}')
    back = types.InlineKeyboardButton(text='Back', callback_data=f'back {item_id}')

    markup.add(minus_one, orders, plus_one).add(clear, cart).add(back)
    return markup


@bot.callback_query_handler(func=lambda call: True)  # дублирует принт почему-то
def buttons_call(call):
    action = call.data.split()[0]
    item_id = call.data.split()[1]
    user = call.from_user.id
    # print(call)
    conn = db.get_db()
    cur = conn.cursor()
    # print(call)

    if action == "+1":
        cur.execute("""INSERT INTO polls_clientcarts (client_id, product_id)
                        VALUES (?, ?);""", (user, item_id,))
        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=item_keyboard(user, item_id))

    elif action == "clear":
        cur.execute("""DELETE FROM polls_clientcarts
                        WHERE client_id = ? AND product_id = ?;""", (user, item_id,))
        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=item_keyboard(user, item_id))

    # elif action == "-1":
    #     cur.execute("""DELETE FROM polls_clientcarts
    #                     WHERE client_id = ? AND product_id = ?
    #                     LIMIT 1;""", (user, item_id,))
    #     bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
    #                                   reply_markup=item_keyboard(user, item_id))


@bot.inline_handler(func=lambda query: len(query.query) > 0)
def inline_query(query):
    category = query.query
    print(query)
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
            reply_markup=item_keyboard(query.from_user.id, inline_info[0])
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
