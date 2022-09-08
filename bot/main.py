import mariadb
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
    cur.execute("""select * from polls_clients where client_id = ?;""", (user_id,))
    check = cur.next()

    if check is None:
        cur.execute("insert into polls_clients (client_id) values (?);", (user_id,))
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_button = types.KeyboardButton("Phone number", request_contact=True, )
        markup.add(phone_button)
        bot.send_message(chat_id=message.chat.id,
                         text="You are not in DB\nEnter your number by pushing button below",
                         reply_markup=markup)
    else:
        functions.welcome_word(message)


@bot.message_handler(content_types=['contact'])
def check_phone(message):
    conn = db.get_db()
    cur = conn.cursor()

    number = message.contact.phone_number

    if not number.startswith("+"):
        number = "+" + number

    cur.execute("""update polls_clients
                    set
                        client_number = ?
                    where
                        client_id = ?;""", (number, message.from_user.id))
    conn.commit()

    msg = bot.send_message(chat_id=message.chat.id,
                           text="Enter your dental name",
                           reply_markup=telebot.types.ReplyKeyboardRemove())

    bot.register_next_step_handler(message=msg,
                                   callback=name_handler)


def name_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update polls_clients
                    set
                        client_name = ?
                    where
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()

    msg = bot.send_message(chat_id=message.chat.id,
                           text="Enter your address",
                           reply_markup=telebot.types.ReplyKeyboardRemove(selective=False))

    bot.register_next_step_handler(message=msg,
                                   callback=address_handler)


def address_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update polls_clients
                    set
                        client_address = ?
                    where
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()
    functions.welcome_word(message)


@bot.message_handler(regexp="Goods")
def category(message):
    bot.send_message(chat_id=message.chat.id,
                     text="You can choose our goods",
                     reply_markup=functions.keyboard('start'))


@bot.message_handler(regexp="Cart")
def buttons_handler(message):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_clientcarts where client_id = ?;""", (message.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=message.from_user.id,
                                text="You cart is empty")

    message_text, priority_text = functions.cart_function(message)

    bot.send_message(chat_id=message.from_user.id,
                     text=message_text,
                     reply_markup=functions.cart_markup(priority_text))


@bot.message_handler(regexp="Profile")
def order_handler(message):
    bot.send_message(chat_id=message.chat.id,
                     text="Here will be inforamtion about your orders.")


@bot.message_handler(regexp="Information")
def info_handler(message):
    bot.send_message(chat_id=message.chat.id,
                     text="Bla bla bla.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("-1"))
def minus_call(call):
    item_id = call.data.split()[1]

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""delete from polls_clientcarts
                        where client_id = ? and product_id = ?
                        limit 1;""", (call.from_user.id, item_id,))

        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=functions.item_keyboard(call.from_user.id, item_id))
    except telebot.apihelper.ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("clean"))
def clean_call(call):

    item_id = call.data.split()[1]

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""delete from polls_clientcarts
                        where client_id = ? and product_id = ?;""", (call.from_user.id, item_id,))
        conn.commit()
        bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                      reply_markup=functions.item_keyboard(call.from_user.id, item_id))
    except telebot.apihelper.ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("+1"))
def plus_call(call):

    item_id = call.data.split()[1]

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""insert into polls_clientcarts (client_id, product_id)
                    values (?, ?);""", (call.from_user.id, item_id,))
    conn.commit()
    bot.edit_message_reply_markup(inline_message_id=call.inline_message_id,
                                  reply_markup=functions.item_keyboard(call.from_user.id, item_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith("back"))
def back_call(call):
    bot.edit_message_text(text="Привет! Я помогу подобрать товар!",
                          inline_message_id=call.inline_message_id,
                          reply_markup=functions.keyboard('start'))


@bot.callback_query_handler(func=lambda call: call.data.startswith("cart"))
def cart_call(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_clientcarts where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=call.from_user.id,
                                text="You bin is empty")

    message_text, priority_text = functions.cart_function(call)

    bot.send_message(chat_id=call.from_user.id,
                     text=message_text,
                     reply_markup=functions.cart_markup(priority_text))


@bot.callback_query_handler(func=lambda call: call.data.startswith("priority"))
def priority_call(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select priority from polls_complete where client_id = ?;""", (call.from_user.id,))
    priority_status = cur.next()[0]

    if priority_status:
        cur.execute("""update polls_complete set priority = ? where client_id = ?;""", (0, call.from_user.id))
        conn.commit()

    else:
        cur.execute("""update polls_complete set priority = ? where client_id = ?;""", (1, call.from_user.id))
        conn.commit()

    message_text, priority_text = functions.cart_function(call)
    bot.edit_message_text(text=message_text,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          reply_markup=functions.cart_markup(priority_text))


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete"))
def delete_call(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from polls_clientcarts
                    where client_id = ?;""", (call.from_user.id,))
    cur.execute("""delete from polls_complete
                    where client_id = ?;""", (call.from_user.id,))
    conn.commit()
    bot.edit_message_text(text="You cart is empty",
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmation"))
def accept_call(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_complete where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        cur.execute("""insert into polls_complete (client_id) values (?);""", (call.from_user.id,))

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter full name of the patient")
    bot.register_next_step_handler(message=msg,
                                   callback=patient_handler)


def patient_handler(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update polls_complete set patient_name = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter the term")
    bot.register_next_step_handler(message=msg,
                                   callback=deadline_handler)


def deadline_handler(call):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update polls_complete set term = ? where client_id = ?;""", (call.text, call.from_user.id))
    except mariadb.OperationalError:
        bot.send_message(chat_id=call.from_user.id,
                         text="Bad term")  # fix~!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        pass
    conn.commit()

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter the time")
    bot.register_next_step_handler(message=msg,
                                   callback=term_time_handler)


def term_time_handler(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update polls_complete set term_time = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    bot.send_message(chat_id=call.from_user.id,
                     text="Leave description?",
                     reply_markup=functions.yes_no())


@bot.callback_query_handler(func=lambda call: call.data.startswith("yes"))
def yes_call(call):
    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter description")
    bot.register_next_step_handler(message=msg,
                                   callback=functions.description_handler)


@bot.callback_query_handler(func=lambda call: call.data.startswith(("no", "accept")))
def confirmation_call(call):
    functions.confirmation(call)


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


if __name__ == '__main__':
    bot.polling(none_stop=True)
