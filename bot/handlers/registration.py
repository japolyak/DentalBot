from ..bot_token import bot
from .. import functions
from telebot import types
from .. import db


def start_move(message):
    """
    Sends message in reply to /start command
    Starts registration funnel with new customer by asking to share the number
    """

    user_id = message.from_user.id

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from  shop_clients where client_id = ?;""", (user_id,))
    user_exists = cur.next()

    if not user_exists:
        cur.execute("insert into  shop_clients (client_id, client_name, client_number, client_address)"
                    "values (?, ?, ?, ?);", (user_id, "Human", "+1234567890", "Earth"))
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_button = types.KeyboardButton(text="Phone number", request_contact=True, )
        markup.add(phone_button)
        bot.send_message(chat_id=message.chat.id,
                         text="You are not yet our customer\nEnter your number by pushing button below",
                         reply_markup=markup)
    else:
        functions.welcome_word(message)


def check_phone(message):
    """
    Responds to sharing number, updates it and activates the next registration step - getting a name
    """

    conn = db.get_db()
    cur = conn.cursor()

    number = message.contact.phone_number

    if not number.startswith("+"):
        number = "+" + number

    cur.execute("""update  shop_clients
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
    """
    Responds to sharing name, updates it and activates the next registration step - getting an address
    """

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update  shop_clients
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
    """
    Responds to sharing address, updates it and sends welcome word
    """
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update  shop_clients
                    set
                        client_address = ?
                    where
                        client_id = ?;""", (message.text, message.from_user.id))
    conn.commit()
    functions.welcome_word(message)


def init_bot():
    bot.register_message_handler(callback=start_move, commands=['start'])
    bot.register_message_handler(callback=check_phone, content_types=['contact'])
