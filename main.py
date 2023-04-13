from init import *
from flask import Flask, request
from src.user.user_handlers import user_bp
from src.admin.admin_handlers import admin_bp
from src.chat.chat_handlers import chat_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

config_init()
database_init()

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)

@app.before_request
def before_request():
    form_data = request.form
    logger_common.info(f'Received request: {request.method} {request.path}, form_data: {form_data}')
    g.session = session_factory()

@app.teardown_request
def teardown_request(exception):
    g.session.close()
    g.pop('session', None)

if __name__ == '__main__':
    app.run(host=main_config.server, port=main_config.port)
