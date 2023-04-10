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
    remaining_balance = (user_balance.total_recharge - user_balance.consumed_amount) if user_balance else 0
    remaining_balance = remaining_balance if remaining_balance >= 0 else 0
    if remaining_balance <= 0:
        response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, "Insufficient balance")
        return jsonify(response_data)

    content_obj = gpt_content(prompt=message)

    if content_obj is None:
        response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, "Error processing content")
        return jsonify(response_data)

    content = content_obj.text
    # tokens_consumed = content_obj.usage["total_tokens"]

    # success, error = UserBalance.update(session, conditions={"user_id": user.id},
    #                                     updates={"consumed_amount": UserBalance.consumed_amount + tokens_consumed})
    # if not success:
    #     response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, error)
    #     return jsonify(response_data)

    response_data = ErrorCode.success({'content': content})
    return jsonify(response_data)

@chat_bp.route('/history/<int:channel_id>', methods=['GET'])
def get_history(channel_id):
    token = request.args.get('token')
    try:
        user = User.query(session, token=token)
        if not user:
            response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")
            return jsonify(response_data)

        chat_history = ChatMessage.query_all(session, user_id=user, channel_id=channel_id)
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
        response_data = ErrorCode.error(ErrorCode.ERROR_INTERNAL_SERVER, "Error getting chat history")
        return jsonify(response_data)

@chat_bp.route('/channels', methods=['GET'])
def get_channels():
    token = request.args.get('token')
    try:
        user = User.query(session, token=token)
        if not user:
            response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")
            return jsonify(response_data)

        channels = ChatChannel.get_channels_by_user(session, user.id)
        response_data = ErrorCode.success({'channels': [channel.serialize() for channel in channels]})
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error while getting channels: {str(e)}")
        response_data = ErrorCode.error(ErrorCode.ERROR_INTERNAL_SERVER, "Error getting channels")
        return jsonify(response_data)

# 删除用户聊天频道
@chat_bp.route('/channel/<int:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    token = request.args.get('token')
    try:
        user = User.query(session, token=token)
        if not user:
            response_data = ErrorCode.error(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")
            return jsonify(response_data)

        success, error = ChatChannel.delete_channel(session, channel_id)
        if success:
            response_data = ErrorCode.success({"message": "Channel deleted successfully"})
            return jsonify(response_data)
        else:
            response_data = ErrorCode.error(ErrorCode.ERROR_INTERNAL_SERVER, error)
            return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error while deleting channel: {str(e)}")
        response_data = ErrorCode.error(ErrorCode.ERROR_INTERNAL_SERVER, "Error deleting channel")
        return jsonify(response_data)