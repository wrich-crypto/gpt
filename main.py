from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer
from init import *
from flask import Flask, request
from src.user.user_handlers import user_bp
from src.admin.admin_handlers import admin_bp
from src.chat.chat_handlers import chat_bp
from flask_cors import CORS

print('init app')
app = Flask(__name__)
CORS(app)

print('config_init')
config_init()
print('database_init')
database_init()

print('init register')
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
    print('server begin')
    WSGIServer((main_config.server, main_config.port), app).serve_forever()
    # app.run(host=main_config.server, port=main_config.port)
    print('server end')