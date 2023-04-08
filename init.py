from package.database.sql import *
from config.config import Config
from package.common.log import *
from package.common.error import *
from flask import jsonify
from package.common.token import generate_token

logger = Logger('gpt', log_to_file=True)
main_config = Config('config.json')
database = MySQLDatabase(
            host=main_config.db_server,
            port=main_config.db_port,
            user=main_config.db_username,
            password=main_config.db_password,
            database=main_config.db_name
        )

def config_init():
    pass

def database_init():
    global database

    try:
        database.connect()
    except Exception as e:
        print(f"Error connecting to database: {e}")