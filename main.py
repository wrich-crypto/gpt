from flask import Flask
from src.user.user_handlers import user_bp
from src.admin.admin_handlers import admin_bp
from src.chat.chat_handlers import chat_bp
from init import *

app = Flask(__name__)

database_init()
config_init()

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)

if __name__ == '__main__':
    app.run()
