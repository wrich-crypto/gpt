from .chat_routes import *
from package.chatgpt.gpt import *
from init import *

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    channel = request.form.get('channel')
    message = request.form.get('message')
    timestamp = request.form.get('timestamp')
    messageId = request.form.get('messageId')
    extras = request.form.get('extras')
    print(f'channel:{channel}, message:{message}, timestamp:{timestamp}, messageId:{messageId}, extras:{extras}')

    # validate the parameters
    # ...

    response_data = ErrorCode.success()
    return jsonify(response_data)
