import mariadb
import sys
import os
import logging

conn = None


def get_db():
    global conn
    
    if not conn:
        try:
            conn = mariadb.connect(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                database=os.getenv("DB_DB")
            )

        except mariadb.Error as e:
            logging.critical(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    return conn
