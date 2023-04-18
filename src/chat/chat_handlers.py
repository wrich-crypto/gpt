from .chat_routes import *
from package.chatgpt.uchatgpt import *
from .chat_module import *
from ..user.user_module import *
import json


def create_stream_with_retry(message, channel=None, max_attempts=None):
    if max_attempts is None:
        max_attempts = len(hot_config.token_cycle)

    for _ in range(max_attempts):
        access_token = hot_config.get_next_api_key()
        print(access_token)

        if access_token is None or access_token.strip() == '':
            break

        chat_api = ChatAPI(access_token)

        channel_id = channel if channel and channel.strip() != "" else generate_uuid()
        create_stream_response = chat_api.create_stream(message, channel_id)
        print(f'create_stream_response:{create_stream_response}')

        if create_stream_response and str(create_stream_response["code"]) == '0':
            logger.info(f'chat gpt response: {create_stream_response}')
            stream_id = create_stream_response["data"]["streamId"]
            return chat_api.get_stream(stream_id)
        else:
            logger.error(f'chat gpt error: {create_stream_response}')
            hot_config.remove_api_key(access_token)

    raise ValueError("Failed to create stream after maximum attempts.")

def generate(channel, message, token, messageId, tokens_consumed):
    try:
        channel = channel
        stream_response = create_stream_with_retry(message, channel, 3)

        content = ''
        for chunk in stream_response.iter_content(chunk_size=1024):
            if chunk:
                decoded_chunk = chunk.decode("utf-8")
                decoded_chunk_obj = DecodedChunk(decoded_chunk)

                if decoded_chunk_obj.event == 'message':
                    content = content + decoded_chunk_obj.data
                yield decoded_chunk

        new_session = session_factory()

        user = User.query(new_session, token=token)

        if not user:
            logger.error(f'Invalid token, token:{token}')
            return

        if ChatChannel.exists(new_session, channel_id=channel, user_id=user.id, status=status_success) is False:
            ChatChannel.upsert(new_session, {"channel_id": channel, "user_id": user.id},
                               {"channel_id": channel, "user_id": user.id,
                                "status": status_success, "title": message})

        ChatMessage.create(new_session, user_id=user.id, channel_id=channel, message_id=messageId,
                           question=message, answer=content, tokens_consumed=tokens_consumed)
        new_session.close()

    except Exception as e:
        logger.error(e)
        yield f"data: {json.dumps(error_response(ErrorCode.ERROR_INTERNAL_SERVER, 'Internal server error'))}\n\n"
        # yield json.dumps(error_response(ErrorCode.ERROR_INTERNAL_SERVER, 'Internal server error'))

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    try:
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
            logger.error('handle_chat_textchat Insufficient balance')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Insufficient balance")

        tokens_consumed = 500
        tokens_consumed = Decimal(tokens_consumed)

        success, error = UserBalance.update(session, conditions={"user_id": user.id},
                                            updates={"consumed_amount": user_balance.consumed_amount + tokens_consumed})
        if not success:
            logger.error('handle_chat_textchat UserBalance.update error:{error}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, error)

        headers = {
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return Response(generate(channel, message, token, messageId, tokens_consumed), headers=headers)
    except Exception as e:
        logger.error(f"handle_chat_textchat error:{e}")

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
            channels_data.append({"id": channel.id,"channel_id": channel.channel_id, "title": channel.title})

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
