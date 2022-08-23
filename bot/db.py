import mariadb
import sys

def get_db():
    try:
        conn = mariadb.connect(
            user="root",
            password="R1dNAUKRa1NA",
            host="127.0.0.1",
            port=3306,
            database="app_orders"
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return conn
