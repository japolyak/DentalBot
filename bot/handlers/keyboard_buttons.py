from ..bot_token import bot
from .. import db
from ..markups import catalogue_markup, cart_markup
from ..functions import items_in_cart


def goods_handler(message):

    bot.send_message(chat_id=message.chat.id,
                     text="You can choose your goods",
                     reply_markup=catalogue_markup())


def cart_handler(message):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("""select * from bot_shop.shop_clientcarts where client_id = ?;""", (message.from_user.id,))
    check = cur.next()

    if not check:
        return bot.send_message(chat_id=message.from_user.id,
                                text="You cart is empty")

    message_text, priority_text = items_in_cart(message)

    bot.send_message(chat_id=message.from_user.id,
                     text=message_text,
                     reply_markup=cart_markup(priority_text))


def profile_handler(message):

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("select * from bot_shop.shop_orders where client_id = ?;", (message.from_user.id, ))

    existence = cur.next()

    if not existence:

        cur.execute("select client_name, client_address from bot_shop.shop_clients where client_id = ?;", (message.from_user.id, ))

        info = cur.next()

        bot.send_message(chat_id=message.chat.id,
                         text=f"Hi, {info[0]} from {info[1]}!\nYou haven't yet placed any orders.")

        return

    cur.execute("""select
                        bot_shop.shop_clients.client_name as client,
                        bot_shop.shop_clients.client_address as adress,
                        a.count as count
                    from bot_shop.shop_clients
                    inner join (select
                                    client_id,
                                    count(*) as "count"
                                from bot_shop.shop_orders
                                where client_id = ?
                                group by client_id) as a
                    on bot_shop.shop_clients.client_id = a.client_id
                    where bot_shop.shop_clients.client_id = ?
                    group by
                        client,
                        adress,
                        count;""", (message.from_user.id, message.from_user.id))

    info = cur.next()

    bot.send_message(chat_id=message.chat.id,
                     text=f"Hi, {info[0]} from {info[1]}!\nYou have already placed {info[2]} orders.")


def info_handler(message):

    bot.send_message(chat_id=message.chat.id,
                     text="""
Hi, I'm Dental Bot!

At first sight I'm simple Bot, but You can dig deeper and catch a sight of unseen.
I was built on Python's TelegramBotApi framework with using of MariaDB database wherein data is stored.
My main role is to process and confirmation orders from dental offices, but i can be modified on your personal needs.

P.S.
If You want to have a quick word with my founder - dm him @japolyak""")


def init_bot():
    bot.register_message_handler(callback=goods_handler, regexp="Goods")
    bot.register_message_handler(callback=cart_handler, regexp="Cart")
    bot.register_message_handler(callback=profile_handler, regexp="Profile")
    bot.register_message_handler(callback=info_handler, regexp="Information")
