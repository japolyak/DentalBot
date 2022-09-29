from . import db, functions
from telebot import types


def item_keyboard(person_id, item_id):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select
                    bot_shop.shop_products.price as price,
                    count(*) as "count"
                    from bot_shop.shop_clientcarts
                    inner join bot_shop.shop_products
                    on bot_shop.shop_clientcarts.product_id = bot_shop.shop_products.id
                    where bot_shop.shop_clientcarts.product_id = ? and bot_shop.shop_clientcarts.client_id = ?
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
    clear = types.InlineKeyboardButton(text='Clear', callback_data=f'clear {item_id}')
    cart = types.InlineKeyboardButton(text=f'{price * quantity}₴', callback_data=f'cart')
    back = types.InlineKeyboardButton(text='Back to catalogue', callback_data=f'back')

    markup.add(minus_one, orders, plus_one).add(clear, cart).add(back)

    return markup


def cart_markup(text):

    markup = types.InlineKeyboardMarkup()

    edit = types.InlineKeyboardButton(text='Edit', callback_data='edit')
    clean = types.InlineKeyboardButton(text='Clean', callback_data='delete')
    priority = types.InlineKeyboardButton(text=text, callback_data='priority')
    confirm = types.InlineKeyboardButton(text='Confirm order', callback_data='confirmation')

    markup.add(edit, clean).add(priority).add(confirm)

    return markup


def leave_description_markup():

    markup = types.InlineKeyboardMarkup()

    yes = types.InlineKeyboardButton(text="Yes", callback_data="yes")
    no = types.InlineKeyboardButton(text="No", callback_data="no")

    markup.add(yes, no)

    return markup


def order_confirmation_markup():

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


def catalogue_markup():

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select distinct category from bot_shop.shop_products;""")
    list_of_goods = []

    for row in cur:
        list_of_goods.append(row[0])

    buttons = []

    for good in list_of_goods:
        buttons.append(types.InlineKeyboardButton(text=good,
                                                  switch_inline_query_current_chat=good))

    markup = types.InlineKeyboardMarkup(functions.buttons_menu(buttons, n_cols=1))

    return markup
