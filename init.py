from package.database.sql import *

database = MySQLDatabase(host='localhost', port=3306, user='root', password='password', database='my_database')

def database_init():
    # database = MySQLDatabase(host='localhost', port=3306, user='root', password='password', database='my_database')
    database.connect()