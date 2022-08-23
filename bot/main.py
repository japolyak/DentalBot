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


@bot.message_handler(regexp="Кошик")
def buttons_handler(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""SELECT *
                    FROM polls_clientcarts
                    WHERE client_id = ?;""", (message.from_user.id, ))

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
        list_of_goods = ['Ceramet', 'ZrO2',
                         'Nonmetal ceramic', 'Nonmetal ceramic E.max',
                         'Wax model', 'Digital model',
                         'Bugel prosthesis', 'Kappa', 'Other works']
        buttons = []

        for good in list_of_goods:
            buttons.append(types.InlineKeyboardButton(text=good, callback_data=good))

        markup = types.InlineKeyboardMarkup(buttons_menu(buttons, n_cols=1))
        return markup


def buttons_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


    # kb = types.InlineKeyboardMarkup()
    # if call == 'start':
    #     kb_1 = types.InlineKeyboardButton(text='Ceramet', callback_data='1_1_inline')
    #     kb_2 = types.InlineKeyboardButton(text='ZrO2', callback_data='1_1_inline')
    #     kb_3 = types.InlineKeyboardButton(text='Nonmetal ceramic', callback_data='1_1_inline')
    #     kb_4 = types.InlineKeyboardButton(text='Nonmetal ceramic E.max', callback_data='1_1_inline')
    #     kb_5 = types.InlineKeyboardButton(text='Wax model', callback_data='1_1_inline')
    #     kb_6 = types.InlineKeyboardButton(text='Digital model', callback_data='1_1_inline')
    #     kb_7 = types.InlineKeyboardButton(text='Bugel prosthesis', callback_data='1_1_inline')
    #     kb_8 = types.InlineKeyboardButton(text='Kappa', callback_data='1_1_inline')
    #     kb_9 = types.InlineKeyboardButton(text='Other works', callback_data='1_1_inline')
    #     kb.add(kb_1, kb_2, kb_3, kb_4, kb_5, kb_6, kb_7, kb_8, kb_9)
    #     print(type(kb))
    #     print(kb)
    #     return kb
    # elif call == 'subcategory':
    #     kb_2 = types.InlineKeyboardButton(text='2_1_inline', callback_data='2_1_inline')
    #     kb.add(kb_2)
    #     return kb
    # elif call == 'product':
    #     kb_3 = types.InlineKeyboardButton(text='3_1_inline', callback_data='3_1_inline')
    #     kb.add(kb_3)
    #     return kb


@bot.message_handler(regexp="Товари")
def category(message):
    bot.send_message(message.chat.id, "Привет! Я помогу подобрать товар!", reply_markup=keyboard('start'))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == '1_1_inline':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='подкатегория', reply_markup=keyboard('subcategory'))
    elif call.data == '2_1_inline':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='товар', reply_markup=keyboard('product'))
    elif call.data == '3_1_inline':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Описание товара')
        bot.send_photo(call.message.chat.id,
                       'https://cs13.pikabu.ru/images/big_size_comm/2020-06_3/159194100716237333.jpg')


if __name__ == '__main__':
    bot.polling(none_stop=True)
