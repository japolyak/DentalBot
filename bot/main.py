import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
import mariadb
import db
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
                         text="You are not yet our customer\nEnter your number by pushing button below",
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

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select
                        polls_clients.client_name as client,
                        polls_clients.client_address as adress,
                        a.count as count
                    from polls_clients
                    inner join (select
                                    client_id,
                                    count(*) as "count"
                                from polls_orders
                                where client_id = ?
                                group by client_id) as a
                    on polls_clients.client_id = a.client_id
                    where polls_clients.client_id = ?
                    group by
                        client,
                        adress,
                        count;""", (message.from_user.id, message.from_user.id))

    info = cur.next()

    bot.send_message(chat_id=message.chat.id,
                     text=f"Hi, {info[0]} from {info[1]}!\nYou placed already {info[2]} orders.")


@bot.message_handler(regexp="Information")
def info_handler(message):

    bot.send_message(chat_id=message.chat.id,
                     text="""
Hi, I'm Dental Bot!

At first sight I'm simple Bot, but You can dig deeper and catch a sight of unseen.
I was built on Python's TelegramBotApi framework with using of MariaDB database wherein data is stored.
My main role is to process and confirmation orders from dental offices, but i can be modified on your personal needs.
 
P.S.
If You want to have a quick word with my founder - dm him @japolyak""")


# start of items keyboard
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
    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("quantity"))
def quantity_handler(call):

    item_id = call.data.split()[1]

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter quantity")
    edit_msg = msg.id
    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=entered_quantity,
                                              edit_msg=edit_msg,
                                              item_id=item_id,
                                              edit_markup=call.inline_message_id)


def entered_quantity(call, edit_msg, item_id, edit_markup):

    try:
        quantity = int(call.text)

    except ValueError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)

        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="You should enter numbers")

        except ApiTelegramException:
            pass

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=entered_quantity,
                                                  edit_msg=edit_msg,
                                                  item_id=item_id,
                                                  edit_markup=edit_markup)
        return

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from polls_clientcarts where client_id = ? and product_id = ?;""", (call.from_user.id, item_id))

    while quantity != 0:
        quantity -= 1
        cur.execute("""insert into polls_clientcarts (client_id, product_id) values (?, ?);""", (call.from_user.id, item_id))

    conn.commit()

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=edit_msg,
                          text="Nice")

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)

    bot.edit_message_reply_markup(inline_message_id=edit_markup,
                                  reply_markup=functions.item_keyboard(call.from_user.id, item_id))


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
    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "cart")
def cart_call(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_clientcarts where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=call.from_user.id,
                                text="You cart is empty")

    message_text, priority_text = functions.cart_function(call)

    bot.send_message(chat_id=call.from_user.id,
                     text=message_text,
                     reply_markup=functions.cart_markup(priority_text))


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_call(call):

    bot.edit_message_text(text="Hi, You can choose one of our goods!",
                          inline_message_id=call.inline_message_id,
                          reply_markup=functions.keyboard('start'))
# finish of items keyboard


# start of carts keyboard
@bot.callback_query_handler(func=lambda call: call.data == "edit")
def edit_items(call):

    functions.edit_markup(call)


# start of editing keyboard
@bot.callback_query_handler(func=lambda call: call.data.startswith("item"))
def secelt_item(call):

    row_id = int(call.data.split()[1])
    functions.cart_edit_markup(call=call, row_id=row_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("minus"))
def editable_minus(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""delete from polls_clientcarts
                        where client_id = ? and product_id = ?
                        limit 1;""", (call.from_user.id, item_id,))

        conn.commit()

        try:
            functions.cart_edit_markup(call=call, row_id=row_id)

        except TypeError:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=call.message.id,
                                  text="Your cart is empty")

    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("rewrite"))
def rewrite_quantity(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter quantity")
    edit_msg = msg.id
    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=next_rewrite_quantity,
                                              edit_msg=edit_msg,
                                              item_id=item_id,
                                              row_id=row_id,
                                              cart_call=call)


def next_rewrite_quantity(call, edit_msg, item_id, row_id, cart_call):

    try:
        quantity = int(call.text)

    except ValueError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)

        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="You should enter numbers")

        except ApiTelegramException:
            pass

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=next_rewrite_quantity,
                                                  edit_msg=edit_msg,
                                                  item_id=item_id,
                                                  row_id=row_id,
                                                  cart_call=cart_call)
        return

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from polls_clientcarts where client_id = ? and product_id = ?;""",
                (call.from_user.id, item_id))

    while quantity != 0:
        quantity -= 1
        cur.execute("""insert into polls_clientcarts (client_id, product_id) values (?, ?);""",
                    (call.from_user.id, item_id))

    conn.commit()

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=edit_msg,
                          text="Nice")

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)
    try:
        functions.cart_edit_markup(call=cart_call, row_id=row_id)

    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("plus"))
def editable_minus(call):

    item_id = call.data.split()[1]
    row_id = int(call.data.split()[2])

    try:
        conn = db.get_db()
        cur = conn.cursor()

        cur.execute("""insert into polls_clientcarts (client_id, product_id)
                        values (?, ?);""", (call.from_user.id, item_id,))

        conn.commit()

        functions.cart_edit_markup(call=call, row_id=row_id)

    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "continue")
def back_to_goods(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text="You can choose our goods",
                          reply_markup=functions.keyboard('start'))


@bot.callback_query_handler(func=lambda call: call.data.startswith("forward"))
def edit_items(call):

    row_id = int(call.data.split()[1]) + 1
    functions.edit_markup(call=call, row_id=row_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("reaward"))
def edit_items(call):

    row_id = int(call.data.split()[1]) - 1
    functions.edit_markup(call=call, row_id=row_id)


@bot.callback_query_handler(func=lambda call: call.data == "finish")
def close_editing(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_clientcarts where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=call.from_user.id,
                                text="You bin is empty")

    message_text, priority_text = functions.cart_function(call)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=message_text,
                          reply_markup=functions.cart_markup(priority_text))
# finish of editing keyboard


@bot.callback_query_handler(func=lambda call: call.data == "priority")
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


@bot.callback_query_handler(func=lambda call: call.data == "delete")
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


@bot.callback_query_handler(func=lambda call: call.data == "confirmation")
def accept_call(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from polls_complete where client_id = ?;""", (call.from_user.id,))
    check = cur.next()

    if not check:
        cur.execute("""insert into polls_complete (client_id) values (?);""", (call.from_user.id,))
        conn.commit()

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter full name of the patient")

    dell_msg = msg.id

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=patient_handler,
                                              dell_msg=dell_msg)


def patient_handler(call, dell_msg):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""update polls_complete set patient_name = ? where client_id = ?;""", (call.text, call.from_user.id))
    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=dell_msg)

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter the date")

    edit_msg = msg.id

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=deadline_handler,
                                              edit_msg=edit_msg)


def deadline_handler(call, edit_msg):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update polls_complete set term = ? where client_id = ?;""", (call.text, call.from_user.id))
        conn.commit()

    except mariadb.OperationalError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)
        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="Enter date like this - yyyy-mm-dd")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=deadline_handler,
                                                  edit_msg=edit_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)

    msg = bot.send_message(chat_id=call.from_user.id,
                           text="Enter the time")

    edit_msg = msg.id

    bot.register_next_step_handler(message=msg,
                                   callback=term_time_handler,
                                   edit_msg=edit_msg)


def term_time_handler(call, edit_msg):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update polls_complete set term_time = ? where client_id = ?;""", (call.text, call.from_user.id))
        conn.commit()

    except mariadb.OperationalError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)
        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=edit_msg,
                                  text="Enter time like this - hh:mm")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=term_time_handler,
                                                  edit_msg=edit_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=edit_msg)

    bot.send_message(chat_id=call.from_user.id,
                     text="Leave description?",
                     reply_markup=functions.yes_no())
# finish of carts keyboard


@bot.callback_query_handler(func=lambda call: call.data == "yes")
def yes_call(call):

    msg = bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.id,
                                text="Enter description")

    bot.register_next_step_handler(message=msg,
                                   callback=functions.description_handler)


@bot.callback_query_handler(func=lambda call: call.data == "no")
def show_order_call(call):

    text = functions.confirmation_text(call)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=text,
                          reply_markup=functions.confirmation_markup())


# start of the confirmation keyboard
@bot.callback_query_handler(func=lambda call: call.data == "accept")
def show_order_call(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=functions.accept(call))


@bot.callback_query_handler(func=lambda call: call.data == "correct")
def edit_tech_info(call):

    bot.edit_message_text(text="Choose what do you whant to change",
                          chat_id=call.from_user.id,
                          message_id=call.message.id,
                          reply_markup=functions.edit_details_markup())


# start of the correct keyboard
@bot.callback_query_handler(func=lambda call: call.data == "fullname")
def edit_fullname(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new fullname of the patient")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=functions.new_fullname_description,
                                              back_msg=back_msg.message_id,
                                              field=call.data)


@bot.callback_query_handler(func=lambda call: call.data == "day")
def edit_fullname(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new term")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=new_term,
                                              back_msg=back_msg.message_id)


def new_term(call, back_msg):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update polls_complete set term = ? where client_id = ?;""", (call.text, call.from_user.id))
        conn.commit()

    except mariadb.OperationalError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)
        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=back_msg,
                                  text="Enter date like this - yyyy-mm-dd")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=new_term,
                                                  back_msg=back_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=back_msg,
                          text=functions.confirmation_text(call),
                          reply_markup=functions.confirmation_markup())


@bot.callback_query_handler(func=lambda call: call.data == "time")
def edit_fullname(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new time")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=new_time,
                                              back_msg=back_msg.message_id)


def new_time(call, back_msg):

    conn = db.get_db()
    cur = conn.cursor()

    try:
        cur.execute("""update polls_complete set term_time = ? where client_id = ?;""", (call.text, call.from_user.id))
        conn.commit()

    except mariadb.OperationalError:
        bot.delete_message(chat_id=call.from_user.id,
                           message_id=call.message_id)
        try:
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=back_msg,
                                  text="Enter time like this - hh:mm")

        except ApiTelegramException:
            pass
        conn.close()

        bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                                  callback=new_term,
                                                  back_msg=back_msg)
        return

    conn.commit()

    bot.delete_message(chat_id=call.from_user.id,
                       message_id=call.message_id)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=back_msg,
                          text=functions.confirmation_text(call),
                          reply_markup=functions.confirmation_markup())


@bot.callback_query_handler(func=lambda call: call.data == "description")
def edit_fullname(call):

    back_msg = bot.edit_message_text(chat_id=call.from_user.id,
                                     message_id=call.message.id,
                                     text="Enter new description")

    bot.register_next_step_handler_by_chat_id(chat_id=call.from_user.id,
                                              callback=functions.new_fullname_description,
                                              back_msg=back_msg.message_id,
                                              field=call.data)


@bot.callback_query_handler(func=lambda call: call.data == "return")
def edit_tech_info(call):

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text=functions.confirmation_text(call),
                          reply_markup=functions.confirmation_markup())
# finish of the correct keyboard


@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_order(call):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""delete from polls_complete where client_id = ?;""", (call.from_user.id, ))
    cur.execute("""delete from polls_clientcarts where client_id = ?;""", (call.from_user.id,))
    conn.commit()

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text="Your order was canceled")
# finish of the confirmation keyboard


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
            reply_markup=functions.item_keyboard(query.from_user.id, inline_info[0]))

        inline_items.append(but)
        inline_id += 1

    bot.answer_inline_query(query.id, inline_items)


if __name__ == '__main__':
    bot.polling(none_stop=True)
