﻿# Python Dental-Bot-shop

This Bot allows dentist offices accept orders directly from Telegram messenger.
Fillong of order can be divided into next steps:

1. Registration of a new user
2. Choosing a product to order
3. Interaction with the product
4. Looking over or editing a cart
5. Getting order details (name of the patient, date, time and description)
6. Order confirmation or editing details

Bot was developed with Python TelegramBotApi framework and uses MariaDB to store the data. Database tables were created in the bot_admin project with the help of Django ORM.

Before runnig Bot it's necessary to change the next features in BotFather:

* `/setrivacy` - change from ENABLED to DISABLED
* `/setinline` - enable inline queries

This project can be also deployed in Docker container on server. To lounch this project use this sample docker-compose file:

```
version: "3.7"

    services:
  bot:
    image: ghcr.io/japolyak/dentalbot:main
    depends_on: [ "db" ]
    restart: always
    environment:
      PYTHONUNBUFFERED: 1
      BOT_TOKEN: YourTelegramBotToken
      DB_USER: YourDBUsername
      DB_PASS: YourDBPassword
      DB_HOST: db
      DB_PORT: YourDBPort
      DB_DB: NameOfYourDatabase

  db:
    image: mariadb
    restart: always
    volumes:
      - ./my.cnf:/etc/mysql/conf.d/my.cnf
    ports:
      - YourDBPort
    environment:
      MARIADB_ROOT_PASSWORD: YourDBRootPassword
  ```
