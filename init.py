from package.database.sql import *
from config.config import Config
from package.common.log import *
from package.common.token import hash_token
from package.common.error import *
from flask import jsonify
from package.common.token import generate_token
from sqlalchemy import create_engine, Column, Integer, Numeric, ForeignKey, DateTime, String, DECIMAL, TIMESTAMP, Text, Enum
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.orm import sessionmaker  # 导入 sessionmaker


logger = Logger('gpt', log_to_file=True, filename='info.log')
logger_common = Logger('common', log_to_file=True, filename='gate.log')

main_config = Config('config.json')
engine = create_engine(f"mysql+pymysql://{main_config.db_username}:{main_config.db_password}@{main_config.db_server}:{main_config.db_port}/{main_config.db_name}")
Session = sessionmaker(bind=engine)
session = Session()
baseDb = BaseModel()

def config_init():
    pass

def database_init():
    pass