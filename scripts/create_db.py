import os

import pymysql

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '0008')
DB_NAME = os.environ.get('DB_NAME', 'mob')


def main():
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
        print(f'Banco de dados "{DB_NAME}" criado ou já existente.')
    finally:
        connection.close()


if __name__ == '__main__':
    main()
