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

    cur.execute("""select
                    polls_products.price as price,
                    COUNT(*) AS "count"

                    from polls_clientcarts

                    inner join polls_products
                    on polls_clientcarts.product_id = polls_products.id
                    where polls_clientcarts.product_id = ? and polls_clientcarts.client_id = ?

                    GROUP BY price;""", (item_id, person_id))

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
    clear = types.InlineKeyboardButton(text='Clear', callback_data=f'clean {item_id}')
    cart = types.InlineKeyboardButton(text=f'{price * quantity}₴', callback_data=f'cart {item_id}')
    back = types.InlineKeyboardButton(text='Back', callback_data=f'back back')

    markup.add(minus_one, orders, plus_one).add(clear, cart).add(back)
    return markup


def cart_function(message):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_clientcarts where client_id = ?;""", (message.from_user.id, ))
    check = cur.next()

    if not check:
        return bot.send_message(message.from_user.id, "You bin is empty")

    while True:
        cur.execute("""select priority from polls_cart_meta where client_id = ?;""", (message.from_user.id, ))
        priority = cur.next()

        if not priority:
            print("stop")
            cur.execute("""insert into polls_cart_meta (client_id) values (?);""", (message.from_user.id, ))
            conn.commit()
            continue
        break

    cur.execute("""select
                            polls_clientcarts.client_id as client,
                            polls_products.product_name as name,
                            polls_products.price as price,
                            polls_clientcarts.product_id as product_id,
                            COUNT(*) AS "count"
                        from polls_clientcarts
                        inner join polls_products

                        on polls_clientcarts.product_id = polls_products.id
                        where polls_clientcarts.client_id = ?
                        GROUP BY
                            client,
                            product_id,
                            name,
                            price
                        order by product_id;""", (message.from_user.id, ))

    product_list = ""
    total_price = 0
    while True:
        row = cur.next()
        if not row:
            break
        product_list += f"{row[1]}\n{row[4]} pcs x {row[2]} ₴ = {row[4] * row[2]} ₴\n\n"
        total_price += row[4] * row[2]

    if priority[0]:
        priority = 1.3
        priority_text = "Disable priority"
    else:
        priority = 1
        priority_text = "Enable priority"

    text = f"""Cart\n\n----\n{product_list}----\nTogether: {total_price * priority} ₴"""

    return text, priority_text


def cart_markup(text):
    markup = types.InlineKeyboardMarkup()

    edit = types.InlineKeyboardButton(text='Edit', callback_data=f'edit cart')
    clean = types.InlineKeyboardButton(text='Clean', callback_data='cleaning cart')
    priority = types.InlineKeyboardButton(text=text, callback_data='priority cart')
    confirm = types.InlineKeyboardButton(text='Confirm order', callback_data=f'confirmation cart')

    markup.add(edit, clean).add(priority).add(confirm)
    return markup
