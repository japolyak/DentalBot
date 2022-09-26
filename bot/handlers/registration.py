from ..bot_token import bot
from .. import functions
from telebot import types
from .. import db


def start_move(message):
    user_id = message.from_user.id

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from bot_shop.shop_clients where client_id = ?;""", (user_id,))
    check = cur.next()

    if check is None:
        cur.execute("insert into bot_shop.shop_clients (client_id, client_name, client_number, client_address)"
                    "values (?, ?, ?, ?);", (user_id, "Human", "+1234567890", "Earth"))
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_button = types.KeyboardButton("Phone number", request_contact=True, )
        markup.add(phone_button)
        bot.send_message(chat_id=message.chat.id,
                         text="You are not yet our customer\nEnter your number by pushing button below",
                         reply_markup=markup)
    else:
        functions.welcome_word(message)


def check_phone(message):

    conn = db.get_db()
    cur = conn.cursor()

    number = message.contact.phone_number

    if not number.startswith("+"):
        number = "+" + number

    cur.execute("""update bot_shop.shop_clients
                    set
                        client_number = ?
                    where
                        client_id = ?;""", (number, message.from_user.id))
    conn.commit()

    msg = bot.send_message(chat_id=message.chat.id,
                           text="Please, enter your dental name",
                           reply_markup=types.ReplyKeyboardRemove())

    bot.register_next_step_handler(message=msg,
                                   callback=name_handler)


def name_handler(message):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update bot_shop.shop_clients
                    set
                        client_name = ?
                    where
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()

    msg = bot.send_message(chat_id=message.chat.id,
                           text="Enter your address",
                           reply_markup=types.ReplyKeyboardRemove(selective=False))

    bot.register_next_step_handler(message=msg,
                                   callback=address_handler)


def address_handler(message):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update bot_shop.shop_clients
                    set
                        client_address = ?
                    where
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()
    functions.welcome_word(message)


def init_bot():
    bot.register_message_handler(callback=start_move, commands=['start'])
    bot.register_message_handler(callback=check_phone, content_types=['contact'])
