import os

if not os.environ.get('DATABASE_URL', '').startswith('postgres'):
    import pymysql

    pymysql.install_as_MySQLdb()
