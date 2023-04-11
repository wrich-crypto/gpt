from .chat_routes import *
from package.chatgpt.chatgpt import *
from .chat_module import *
from ..user.user_module import *
import json

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

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
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    user_balance = UserBalance.query(session, user_id=user.id)
    remaining_balance = (user_balance.total_recharge - user_balance.consumed_amount) if user_balance else 0
    remaining_balance = remaining_balance if remaining_balance >= 0 else 0
    if remaining_balance <= 0:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Insufficient balance")

    content, tokens_consumed, err = handle_chat(chat_manager=chat_manager, channel_id=channel, user_input=message)

    if err is not None:
        logger.error(f'handle_chat_textchat gpt chat handle_chat error:{err}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER)

    if content is None or content == '':
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Error processing content")

    tokens_consumed = Decimal(tokens_consumed)
    ChatMessage.create(session, user_id=user.id, channel_id=channel, message_id=messageId,
                       question=message, answer=content, tokens_consumed=tokens_consumed)

    success, error = UserBalance.update(session, conditions={"user_id": user.id},
                                        updates={"consumed_amount": user_balance.consumed_amount + tokens_consumed})
    if not success:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, error)

    def generate_response():
        response_data = ErrorCode.success({'content': content})
        yield json.dumps(response_data)
    return Response(stream_with_context(generate_response()), content_type='application/octet-stream')

@chat_bp.route('/history/<string:channel_id>', methods=['GET'])
def get_history(channel_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    try:
        user = User.query(session, token=token)
        if not user:
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        chat_history, e = ChatMessage.query_all(session, limit=100, user_id=user.id, channel_id=channel_id)

        response_data = ErrorCode.success({
            'chat_history': [
                {
                    'user_id': message.user_id,
                    'channel_id': message.channel_id,
                    'message_id': message.message_id,
                    'question': message.question,
                    'answer': message.answer
                } for message in chat_history
            ]
        })
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error while getting chat history: {str(e)}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Error getting chat history")

@chat_bp.route('/channels', methods=['GET'])
def get_channels():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    try:
        user = User.query(session, token=token)
        if not user:
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        channels = ChatChannel.get_channels_by_user(session, user.id)
        response_data = ErrorCode.success({'channels': [channel.serialize() for channel in channels]})
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error while getting channels: {str(e)}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Error getting channels")

# 删除用户聊天频道
@chat_bp.route('/channel/<int:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    try:
        user = User.query(session, token=token)
        if not user:
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        success, error = ChatChannel.delete_channel(session, channel_id)
        if success:
            response_data = ErrorCode.success({"message": "Channel deleted successfully"})
            return jsonify(response_data)
        else:
            return error_response(ErrorCode.ERROR_INTERNAL_SERVER, error)
    except Exception as e:
        logger.error(f"Error while deleting channel: {str(e)}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Error deleting channel")
