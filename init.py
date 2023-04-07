from package.database.sql import *
from config.config import *

database = None
config = None

def config_init():
    global config
    config = Config('config.json')


def database_init():
    global database
    database = MySQLDatabase(host='localhost', port=3306, user='root', password='password', database='my_database')
    database.connect()