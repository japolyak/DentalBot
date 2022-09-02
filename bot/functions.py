from main import *


def welcome_word(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    position_button = types.KeyboardButton("Товари")
    basket_button = types.KeyboardButton("Cart")
    profile_button = types.KeyboardButton("Профіль")
    info_button = types.KeyboardButton("Інфо")

    markup.add(position_button,
               basket_button,
               profile_button,
               info_button)

    bot.send_message(message.chat.id, "Welcome to the club, buddy!", reply_markup=markup)


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
    print(person_id, item_id)

    cur.execute("""select
                    polls_products.price as price,
                    COUNT(*) AS "count"

                    from polls_clientcarts

                    inner join polls_products
                    on polls_clientcarts.product_id = polls_products.id
                    where polls_clientcarts.product_id = ? and polls_clientcarts.client_id = ?

                    GROUP BY price;""", (item_id, person_id))

    # cur.execute("""SELECT COUNT(*)
    #                 FROM polls_clientcarts
    #                 where client_id = ? and product_id = ?;""", (person_id, item_id))
    item_quantity = cur.next()
    # print(item_quantity) выполняется столько раз, сколько элементов категории
    if not item_quantity:
        item_quantity = (0, 0)
    price = item_quantity[0]
    quantity = item_quantity[1]

    markup = types.InlineKeyboardMarkup()

    minus_one = types.InlineKeyboardButton(text='-1', callback_data=f'-1 {item_id}')
    orders = types.InlineKeyboardButton(text=f'{quantity} pcs', callback_data=f'quantity {item_id}')
    plus_one = types.InlineKeyboardButton(text='+1', callback_data=f'+1 {item_id}')
    clear = types.InlineKeyboardButton(text='Clear', callback_data=f'clear {item_id}')
    cart = types.InlineKeyboardButton(text=f'₴ {price * quantity}', callback_data=f'cart {item_id}')
    back = types.InlineKeyboardButton(text='Back', callback_data=f'back back')

    markup.add(minus_one, orders, plus_one).add(clear, cart).add(back)
    return markup


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
