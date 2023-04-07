from flask import Flask
from user.user_handlers import user_bp
from admin.admin_handlers import admin_bp
from chat.chat_handlers import chat_bp

app = Flask(__name__)

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)

if __name__ == '__main__':
    app.run()
