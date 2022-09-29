from bot.bot_token import bot
from bot.handlers import registration, keyboard_buttons,\
    catalogue, item_buttons,\
    cart_buttons, set_description,\
    edit_cart_buttons, edit_details_buttons, confirm_buttons
import logging
logging.basicConfig(encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


if __name__ == '__main__':
    logging.info('Starting bot..')

    logging.info('Initializing database')

    logging.info('Initializing handlers')

    registration.init_bot()
    keyboard_buttons.init_bot()
    catalogue.init_bot()
    item_buttons.init_bot()
    cart_buttons.init_bot()
    set_description.init_bot()
    edit_cart_buttons.init_bot()
    edit_details_buttons.init_bot()
    confirm_buttons.init_bot()

    logging.info('Starting polling')
    bot.polling(none_stop=True)
