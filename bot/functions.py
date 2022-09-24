from main import *


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
                    count(*) as "count"
                    from polls_clientcarts
                    inner join polls_products
                    on polls_clientcarts.product_id = polls_products.id
                    where polls_clientcarts.product_id = ? and polls_clientcarts.client_id = ?
                    group by price;""", (item_id, person_id))

    item_quantity = cur.next()

    if not item_quantity:
        item_quantity = (0, 0)

    price = item_quantity[0]
    quantity = item_quantity[1]

    markup = types.InlineKeyboardMarkup()

    minus_one = types.InlineKeyboardButton(text='-1', callback_data=f'-1 {item_id}')
    orders = types.InlineKeyboardButton(text=f'{quantity} pcs', callback_data=f'quantity {item_id}')
    plus_one = types.InlineKeyboardButton(text='+1', callback_data=f'+1 {item_id}')
    clear = types.InlineKeyboardButton(text='Clear', callback_data=f'clean {item_id}')
    cart = types.InlineKeyboardButton(text=f'{price * quantity}₴', callback_data=f'cart')
    back = types.InlineKeyboardButton(text='Back', callback_data=f'back')

    markup.add(minus_one, orders, plus_one).add(clear, cart).add(back)
    return markup


def cart_function(message):
    conn = db.get_db()
    cur = conn.cursor()

    while True:
        cur.execute("""select priority from polls_complete where client_id = ?;""", (message.from_user.id, ))
        priority_inf = cur.next()

        if not priority_inf:
            cur.execute("""insert into polls_complete (client_id) values (?);""", (message.from_user.id, ))
            conn.commit()
            continue
        break

    cur.execute("""select
                            polls_clientcarts.client_id as client,
                            polls_products.product_name as name,
                            polls_products.price as price,
                            polls_clientcarts.product_id as product_id,
                            count(*) AS "count"
                        from polls_clientcarts
                        inner join polls_products
                        on polls_clientcarts.product_id = polls_products.id
                        where polls_clientcarts.client_id = ?
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


def cart_markup(text):
    markup = types.InlineKeyboardMarkup()

    edit = types.InlineKeyboardButton(text='Edit', callback_data='edit')  # add possibility
    clean = types.InlineKeyboardButton(text='Clean', callback_data='delete')
    priority = types.InlineKeyboardButton(text=text, callback_data='priority')
    confirm = types.InlineKeyboardButton(text='Confirm order', callback_data='confirmation')

    markup.add(edit, clean).add(priority).add(confirm)
    return markup


def yes_no():
    markup = types.InlineKeyboardMarkup()

    yes = types.InlineKeyboardButton(text="Yes", callback_data="yes")
    no = types.InlineKeyboardButton(text="No", callback_data="no")

    markup.add(yes, no)
    return markup


def confirmation_text(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select patient_name, term, term_time, description from polls_complete where client_id = ?;""", (call.from_user.id, ))
    details = cur.next()

    text = f"Patient full name: {details[0]}\nTerm: {details[1]}\nTime: {details[2]}\nDescription: {details[3]}"

    return text


def confirmation_markup():
    markup = types.InlineKeyboardMarkup()

    confirm = types.InlineKeyboardButton(text="Confirm order", callback_data="accept")
    correct = types.InlineKeyboardButton(text="Correct details", callback_data="correct")
    cancel = types.InlineKeyboardButton(text="Cancel order", callback_data="cancel")

    markup.add(confirm).add(correct).add(cancel)
    return markup


def edit_details_markup():
    markup = types.InlineKeyboardMarkup()

    patient = types.InlineKeyboardButton(text="Patient name", callback_data="fullname")
    term = types.InlineKeyboardButton(text="Term", callback_data="day")
    time = types.InlineKeyboardButton(text="Time", callback_data="time")
    desc = types.InlineKeyboardButton(text="Descrition", callback_data="description")
    back = types.InlineKeyboardButton(text="Back", callback_data="return")

    markup.add(patient).add(term).add(time).add(desc).add(back)
    return markup


def new_fullname_description(call, back_msg, field):
    conn = db.get_db()
    cur = conn.cursor()

    if field == "fullname":
        cur.execute("""update polls_complete set patient_name = ? where client_id = ?;""", (call.text, call.from_user.id))
    elif field == "description":
        cur.execute("""update polls_complete set description = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=back_msg,
                          text=confirmation_text(call),
                          reply_markup=confirmation_markup())


def accept(call):
    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""insert into polls_orders (client_id, patient_name, term, term_time, descrition, priority)
                    select client_id, patient_name, term, term_time, description, priority
                    from polls_complete
                    where client_id = ?;""", (call.from_user.id, ))
    row_id = cur.lastrowid

    cur.execute("""insert into polls_order_goods (order_id, product_id, quantity)
                    select
                        ? as client,
                        product_id as product_id,
                        count(*) AS "count"
                    from polls_clientcarts
                    
                    where polls_clientcarts.client_id = ?
                    group by
                        client,
                        product_id
                    order by count;""", (row_id, call.from_user.id,))

    cur.execute("""delete from polls_complete where client_id = ?;""", (call.from_user.id, ))
    cur.execute("""delete from polls_clientcarts where client_id = ?;""", (call.from_user.id,))

    conn.commit()

    cur.execute("""select * from polls_orders where order_id = ?;""", (row_id,))
    common = cur.next()

    priority = 1
    priority_text = "Normal order"

    if common[6]:
        priority = 1.3
        priority_text = "Prioritized order (+30%)"

    cur.execute("""select
                        polls_order_goods.quantity as quantity,
                        polls_products.product_name as name,
                        polls_products.price as price
                    from polls_order_goods
                    inner join polls_products
                    on polls_order_goods.product_id = polls_products.id
                    where polls_order_goods.order_id = ?
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

    cur.execute("""update polls_complete set description = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    text = confirmation_text(call)

    bot.send_message(chat_id=call.from_user.id,
                     text=text,
                     reply_markup=confirmation_markup())


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
                             from polls_clientcarts 
                             where client_id = ?) as b;""", (call.from_user.id,))

    items_quantity = int(cur.next()[0])

    if row_id > items_quantity:
        row_id = 1

    if row_id == 0:
        row_id = items_quantity

    cur.execute("""select row_num, name, price, count, product_id, client from
                        (select row_number() over () as row_num, name, price, count, product_id, client from
                        (select
                            polls_clientcarts.client_id as client,
                            polls_products.product_name as name,
                            polls_products.price as price,
                            polls_clientcarts.product_id as product_id,
                            count(*) AS "count"
                        from polls_clientcarts
                        inner join polls_products
                        on polls_clientcarts.product_id = polls_products.id
                        where polls_clientcarts.client_id = ?
                        group by
                            client,
                            product_id,
                            name,
                            price) as a) as b where row_num = ?;""", (call.from_user.id, row_id))

    return cur.next(), items_quantity, row_id


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