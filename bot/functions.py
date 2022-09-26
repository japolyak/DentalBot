from telebot import types
from .bot_token import bot
from . import db, markups


def welcome_word(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    position_button = types.KeyboardButton("Goods")
    basket_button = types.KeyboardButton("Cart")
    profile_button = types.KeyboardButton("Profile")
    info_button = types.KeyboardButton("Information")

    markup.add(position_button,
               basket_button,
               profile_button,
               info_button)

    bot.send_message(chat_id=message.chat.id,
                     text="Welcome to the club, buddy!",
                     reply_markup=markup)


def buttons_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):

    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, header_buttons)

    if footer_buttons:
        menu.append(footer_buttons)

    return menu


def cart_function(message):
    conn = db.get_db()
    cur = conn.cursor()

    while True:
        cur.execute("""select priority from bot_shop.shop_cartmeta where client_id = ?;""", (message.from_user.id, ))
        priority_inf = cur.next()

        if not priority_inf:
            cur.execute("""insert into bot_shop.shop_cartmeta (client_id, patient_name, deadline, term_time, description, priority)
            values (?, ?, ?, ?, ?, ?);""", (message.from_user.id, "Patient", "2022-09-26", "18:00", "No", False))
            conn.commit()
            continue
        break

    cur.execute("""select
                            bot_shop.shop_clientcarts.client_id as client,
                            bot_shop.shop_products.product_name as name,
                            bot_shop.shop_products.price as price,
                            bot_shop.shop_clientcarts.product_id as product_id,
                            count(*) AS "count"
                        from bot_shop.shop_clientcarts
                        inner join bot_shop.shop_products
                        on bot_shop.shop_clientcarts.product_id = bot_shop.shop_products.id
                        where bot_shop.shop_clientcarts.client_id = ?
                        group by
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

    priority = 1
    priority_text = "Enable priority"

    if priority_inf[0]:
        priority = 1.3
        priority_text = "Disable priority"

    text = f"""Cart\n\n----\n{product_list}----\nTogether: {total_price * priority} ₴"""

    return text, priority_text


def confirmation_text(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select patient_name, deadline, term_time, description from bot_shop.shop_cartmeta where client_id = ?;""", (call.from_user.id, ))
    details = cur.next()

    text = f"Patient full name: {details[0]}\nTerm: {details[1]}\nTime: {details[2]}\nDescription: {details[3]}"

    return text


def new_fullname_description(call, back_msg, field):
    conn = db.get_db()
    cur = conn.cursor()

    if field == "fullname":
        cur.execute("""update bot_shop.shop_cartmeta set patient_name = ? where client_id = ?;""", (call.text, call.from_user.id))
    elif field == "description":
        cur.execute("""update bot_shop.shop_cartmeta set description = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=back_msg,
                          text=confirmation_text(call),
                          reply_markup=markups.confirmation_markup())


def accept(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""insert into bot_shop.shop_orders (client_id, patient_name, deadline, term_time, description, priority)
                    select client_id, patient_name, deadline, term_time, description, priority
                    from bot_shop.shop_cartmeta
                    where client_id = ?;""", (call.from_user.id, ))
    row_id = cur.lastrowid

    cur.execute("""insert into bot_shop.shop_orderedgoods (order_id, product_id, quantity)
                    select
                        ? as client,
                        product_id as product_id,
                        count(*) AS "count"
                    from bot_shop.shop_clientcarts
                    
                    where bot_shop.shop_clientcarts.client_id = ?
                    group by
                        client,
                        product_id
                    order by count;""", (row_id, call.from_user.id,))

    cur.execute("""delete from bot_shop.shop_cartmeta where client_id = ?;""", (call.from_user.id, ))
    cur.execute("""delete from bot_shop.shop_clientcarts where client_id = ?;""", (call.from_user.id,))

    conn.commit()

    cur.execute("""select * from bot_shop.shop_orders where order_id = ?;""", (row_id,))
    common = cur.next()

    priority = 1
    priority_text = "Normal order"

    if common[6]:
        priority = 1.3
        priority_text = "Prioritized order (+30%)"

    cur.execute("""select
                        bot_shop.shop_orderedgoods.quantity as quantity,
                        bot_shop.shop_products.product_name as name,
                        bot_shop.shop_products.price as price
                    from bot_shop.shop_orderedgoods
                    inner join bot_shop.shop_products
                    on bot_shop.shop_orderedgoods.product_id = bot_shop.shop_products.id
                    where bot_shop.shop_orderedgoods.order_id = ?
                    group by
                        name,
                        price,
                        quantity;""", (row_id, ))

    price = 0
    product_list = ""

    while True:
        row = cur.next()
        if not row:
            break
        price += row[0] * row[2] * priority
        product_list += f"{row[0]} pcs x {row[1]} - {row[0] * row[2]} ₴\n"

    text = f"{priority_text} №{row_id}\nDeadline - {common[4]} on {common[3]}\nOrdered goods:\n{product_list}\nTotal summ: {price}"

    return text


def description_handler(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update bot_shop.shop_cartmeta set description = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    text = confirmation_text(call)

    bot.send_message(chat_id=call.from_user.id,
                     text=text,
                     reply_markup=markups.confirmation_markup())


def edit_markup(call, row_id=1):
    n_item, items_quantity, row_id = editable_cart_item(call, row_id)

    markup = types.InlineKeyboardMarkup()

    patient = types.InlineKeyboardButton(text=f"{n_item[3]} pcs.|{n_item[1]}", callback_data=f"item {row_id}")
    back = types.InlineKeyboardButton(text="Back to goods", callback_data="continue")
    back_move = types.InlineKeyboardButton(text="<--", callback_data=f"reaward {row_id}")
    in_item = types.InlineKeyboardButton(text=f"{row_id}/{items_quantity}", callback_data="anything")
    forvard_move = types.InlineKeyboardButton(text="-->", callback_data=f"forward {row_id}")
    finish = types.InlineKeyboardButton(text="Finish editing", callback_data="finish")

    markup.add(patient).add(back).add(back_move, in_item, forvard_move).add(finish)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=f"{n_item[1]}\n{n_item[3]} pcs x {n_item[2]}₴ = {n_item[2] * n_item[3]}₴",
                          reply_markup=markup)


def cart_edit_markup(call, row_id):
    n_item, items_quantity, row_id = editable_cart_item(call, row_id)

    markup = types.InlineKeyboardMarkup()

    minus_one = types.InlineKeyboardButton(text="-1", callback_data=f"minus {n_item[4]} {n_item[0]}")
    quantity = types.InlineKeyboardButton(text=f"{n_item[3]}", callback_data=f"rewrite {n_item[4]} {n_item[0]}")
    plus_one = types.InlineKeyboardButton(text="+1", callback_data=f"plus {n_item[4]} {n_item[0]}")
    back = types.InlineKeyboardButton(text="Back to goods", callback_data="continue")

    back_move = types.InlineKeyboardButton(text="<--", callback_data=f"reaward {row_id}")
    in_item = types.InlineKeyboardButton(text=f"{row_id}/{items_quantity}", callback_data="anything")
    forvard_move = types.InlineKeyboardButton(text="-->", callback_data=f"forward {row_id}")
    finish = types.InlineKeyboardButton(text="Finish editing", callback_data="finish")

    markup.add(minus_one, quantity, plus_one).add(back).add(back_move, in_item, forvard_move).add(finish)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=f"{n_item[1]}\n{n_item[3]} pcs x {n_item[2]}₴ = {n_item[2] * n_item[3]}₴",
                          reply_markup=markup)


def editable_cart_item(call, row_id):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select count(*) 
                        from 
                            (select distinct product_id 
                             from bot_shop.shop_clientcarts 
                             where client_id = ?) as b;""", (call.from_user.id,))

    items_quantity = int(cur.next()[0])

    if row_id > items_quantity:
        row_id = 1

    if row_id == 0:
        row_id = items_quantity

    cur.execute("""select row_num, name, price, count, product_id, client from
                        (select row_number() over () as row_num, name, price, count, product_id, client from
                        (select
                            bot_shop.shop_clientcarts.client_id as client,
                            bot_shop.shop_products.product_name as name,
                            bot_shop.shop_products.price as price,
                            bot_shop.shop_clientcarts.product_id as product_id,
                            count(*) AS "count"
                        from bot_shop.shop_clientcarts
                        inner join bot_shop.shop_products
                        on bot_shop.shop_clientcarts.product_id = bot_shop.shop_products.id
                        where bot_shop.shop_clientcarts.client_id = ?
                        group by
                            client,
                            product_id,
                            name,
                            price) as a) as b where row_num = ?;""", (call.from_user.id, row_id))

    return cur.next(), items_quantity, row_id
