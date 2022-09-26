from ..bot_token import bot
from telebot import types
from .. import db
from ..markups import item_keyboard


def inline_query(query):

    category = query.query
    conn = db.get_db()
    cur = conn.cursor()

    inline_id = 1
    inline_items = []

    cur.execute("""select id, product_name, price  from bot_shop.shop_products where category = ?;""", (category,))

    while True:
        inline_info = cur.next()
        if not inline_info:
            break
        but = types.InlineQueryResultArticle(
            id=f"{inline_id}", title=inline_info[1], description=f"₴ {inline_info[2]}",
            input_message_content=types.InputTextMessageContent(message_text=inline_info[1]),
            reply_markup=item_keyboard(query.from_user.id, inline_info[0]))

        inline_items.append(but)
        inline_id += 1

    bot.answer_inline_query(query.id, inline_items)


def init_bot():
    bot.register_inline_handler(callback=inline_query, func=lambda query: len(query.query) > 0)
