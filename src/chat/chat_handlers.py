from .chat_routes import *
from package.chatgpt.gpt import *
from .chat_module import *
from ..user.user_module import *

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    token = request.form.get('token')
    channel = request.form.get('channel')
    message = request.form.get('message')
    timestamp = request.form.get('timestamp')
    messageId = request.form.get('messageId')
    extras = request.form.get('extras')
    logger.info(f'channel:{channel}, message:{message}, timestamp:{timestamp}, messageId:{messageId}, extras:{extras}')

    if message == '':
        response_data = ErrorCode.success({'content': ''})
        return jsonify(response_data)

    user = User.query(session, token=token)

    if not user:
        response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')
        return jsonify(response_data)

    user_balance = UserBalance.query(session, user_id=user.id)
    remaining_balance = user_balance.remaining_balance if user_balance else 0
    consumed_amount = user_balance.consumed_amount if user_balance else 0

    balance = remaining_balance - consumed_amount
    if balance <= 0:
        response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, "Insufficient balance")
        return jsonify(response_data)

    api_key = main_config.openai_key
    content = gpt_content(api_key=api_key, prompt=message)
    response_data = ErrorCode.success({'content': content})
    return jsonify(response_data)
