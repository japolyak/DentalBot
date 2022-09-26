from bot.bot_token import bot
from bot.handlers import registration, reply_buttons,\
    items_by_cat, item_buttons,\
    cart_buttons, descrition_choice,\
    cart_edit_menu, correct_menu, confirm_buttons
import logging
logging.basicConfig(encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


if __name__ == '__main__':
    logging.info('Starting bot..')

    logging.info('Initializing database')
    # TODO

    logging.info('Initializing handlers')

    registration.init_bot()
    reply_buttons.init_bot()
    items_by_cat.init_bot()
    item_buttons.init_bot()
    cart_buttons.init_bot()
    descrition_choice.init_bot()
    cart_edit_menu.init_bot()
    correct_menu.init_bot()
    confirm_buttons.init_bot()

    logging.info('Starting polling')
    bot.polling(none_stop=True)
