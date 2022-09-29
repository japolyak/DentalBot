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

    cur.execute("""select id, product_name, price  from  shop_products where category = ?;""", (category,))

    for inline_info in cur:
        but = types.InlineQueryResultArticle(
            id=f"{inline_id}", title=inline_info[1], description=f"₴ {inline_info[2]}",
            input_message_content=types.InputTextMessageContent(message_text=inline_info[1]),
            reply_markup=item_keyboard(person_id=query.from_user.id, item_id=inline_info[0]))

        inline_items.append(but)
        inline_id += 1

    bot.answer_inline_query(query.id, inline_items)


def init_bot():
    bot.register_inline_handler(callback=inline_query, func=lambda query: len(query.query) > 0)
