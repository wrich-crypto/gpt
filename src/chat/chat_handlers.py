from .chat_routes import *
from package.chatgpt.uchatgpt import *
from .chat_module import *
from ..user.user_module import *
import json

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
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
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    user_balance = UserBalance.query(session, user_id=user.id)
    remaining_balance = (user_balance.total_recharge - user_balance.consumed_amount) if user_balance else 0
    remaining_balance = remaining_balance if remaining_balance >= 0 else 0
    if remaining_balance <= 0:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Insufficient balance")

    access_token = hot_config.get_next_api_key()
    chat_api = ChatAPI(access_token)

    def generate():
        try:
            channel_id = channel if channel and channel.strip() != "" else generate_uuid()
            create_stream_response = chat_api.create_stream(message, channel_id)
            stream_id = create_stream_response["data"]["streamId"]

            stream_response = chat_api.get_stream(stream_id)
            content = ''
            for chunk in stream_response.iter_content(chunk_size=None):
                if chunk:
                    decoded_chunk = chunk.decode("utf-8")
                    decoded_chunk_obj = DecodedChunk(decoded_chunk)

                    if decoded_chunk_obj.event == 'message':
                        content = content + decoded_chunk_obj.data
                        print(content)
                    yield decoded_chunk

            new_session = session_factory()

            user = User.query(new_session, token=token)

            if not user:
                logger.error(f'Invalid token, token:{token}')
                return

            if ChatChannel.exists(new_session, channel_id=channel_id, user_id=user.id, status=status_success) is False:
                ChatChannel.upsert(new_session, {"channel_id": channel_id, "user_id": user.id},
                                        {"channel_id": channel_id, "user_id": user.id, "status": status_success})

            ChatMessage.create(new_session, user_id=user.id, channel_id=channel, message_id=messageId,
                               question=message, answer=content, tokens_consumed=tokens_consumed)
            new_session.close()

        except Exception as e:
            logger.error(e)
            yield json.dumps(error_response(ErrorCode.ERROR_INTERNAL_SERVER, 'Internal server error'))

    tokens_consumed = 500
    tokens_consumed = Decimal(tokens_consumed)

    success, error = UserBalance.update(session, conditions={"user_id": user.id},
                                        updates={"consumed_amount": user_balance.consumed_amount + tokens_consumed})
    if not success:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, error)

    headers = {
        "Content-Type": "text/event-stream",
        "Transfer-Encoding": "chunked",
        "Cache-Control": "no-cache",
    }
    return Response(generate(), headers=headers)

@chat_bp.route('/history/<string:channel_id>', methods=['GET'])
def get_history(channel_id):
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    try:
        user = User.query(session, token=token)
        if not user:
            logger.error(f'Invalid token, auth_header:{auth_header}')
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
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    try:
        user = User.query(session, token=token)

        if not user:
            logger.error(f'Invalid token, auth_header:{auth_header}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        channels = ChatChannel.get_channels_by_user(session, user_id=user.id, status=status_success)
        channels_data = []
        for channel in channels:
            channels_data.append({"channel_id": channel.channel_id})

        response_data = ErrorCode.success({'channels': channels_data})
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error while getting channels: {str(e)}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Error getting channels")

@chat_bp.route('/channel/<int:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    try:
        user = User.query(session, token=token)
        if not user:
            logger.error(f'Invalid token, auth_header:{auth_header}')
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
