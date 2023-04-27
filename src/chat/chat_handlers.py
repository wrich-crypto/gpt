from .chat_routes import *
from package.chatgpt.uchatgpt import *
from .chat_module import *
from ..user.user_module import *
import json
from flask import Flask, request, Response, stream_with_context

def create_stream_with_retry(message, channel=None, version='3.5', system='', max_attempts=3):
    for _ in range(max_attempts):
        access_token = hot_config.get_next_api_key()
        print(access_token)

        if system is None:
            system = ''

        if access_token is None or access_token.strip() == '':
            break

        chat_api = ChatAPI(access_token)

        channel_id = channel if channel and channel.strip() != "" else generate_uuid()
        create_stream_response = chat_api.create_stream(message, channel_id, version, system)
        print(f'create_stream_response:{create_stream_response}')

        if create_stream_response and str(create_stream_response["code"]) == '0':
            logger.info(f'chat gpt response: {create_stream_response}')
            stream_id = create_stream_response["data"]["streamId"]
            return stream_id, channel_id
        elif str(create_stream_response["code"]) == '1':
            logger.error(f'chat gpt error: {create_stream_response}')
            hot_config.remove_api_key(access_token)
        else:
            logger.error(f'chat gpt error: {create_stream_response}')

    raise ValueError("Failed to create stream after maximum attempts.")

@stream_with_context
def generate(stream_id, user_id):
    try:
        access_token = hot_config.get_next_api_key()
        print(access_token)

        if access_token is None or access_token.strip() == '':
            raise ValueError("Failed to create stream after maximum attempts.")

        chat_api = ChatAPI(access_token)
        stream_response = chat_api.get_stream(stream_id)

        content = ''
        for chunk in stream_response.iter_content(chunk_size=1024):
            if chunk:
                decoded_chunk = chunk.decode("utf-8")
                decoded_chunk_obj = DecodedChunk(decoded_chunk)

                if decoded_chunk_obj.event == 'message':
                    content = content + decoded_chunk_obj.data
                    yield decoded_chunk

        logger.debug(content)
        new_session = session_factory()
        chat_message = ChatMessage.query(new_session, stream_id=stream_id)
        if chat_message:
            ChatMessage.update(new_session, conditions={"stream_id": stream_id}, updates={"answer": content})

        consume_response = chat_api.get_stream_consume(stream_id)
        print(f'consume_response:{consume_response}')

        if consume_response and str(consume_response["code"]) == 0:
            logger.debug(f'chat gpt consume_response response: {consume_response}')
            
            try:
                consume_token_amount = int(consume_response["data"]["token"])
            except Exception as e:
                consume_token_amount = 500
                logger.error(f'enerate - update_user_consumed error:{e}')

            if update_user_consumed(new_session, user_id, consume_token_amount) is False:
                logger.error(f'generate - update_user_consumed user_id:{user_id} consume_token_amount : '
                             f'{consume_token_amount} error')
            else:
                logger.info(f'generate - update_user_consumed user_id:{user_id} consume_token_amount : '
                            f'{consume_token_amount} success')
        else:
            logger.error(f'chat gpt error: {consume_response}')

        new_session.close()

    except Exception as e:
        logger.error(f'generate error {e}')
        yield f"data: {json.dumps(error_response(ErrorCode.ERROR_INTERNAL_SERVER, 'Internal server error'))}\n\n"

@chat_bp.route('/create_stream', methods=['POST'])
def create_stream():
    try:
        new_session = g.session
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error(f'Invalid token, auth_header:{auth_header}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

        token = auth_header[7:]

        user = User.query(new_session, token=token)

        if not user:
            logger.error(f'Invalid token, auth_header:{auth_header}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        data = g.data
        channel_uuid = data.get('channel_id')
        message = data.get('message')
        timestamp = data.get('timestamp')
        extras = data.get('extras')
        version = data.get('version')
        system = data.get('system')

        if balance_valid(new_session, user.id) is False:
            logger.error(f'Insufficient balance, auth_header:{auth_header}, user id:{user.id}')
            return error_response(ErrorCode.ERROR_BALANCE, "Insufficient balance")

        stream_id, channel_uuid = create_stream_with_retry(message, channel_uuid, str(version), system=system)

        if not ChatChannel.exists(new_session, channel_uuid=channel_uuid, user_id=user.id, status=status_success):
            ChatChannel.create(new_session, channel_uuid=channel_uuid, user_id=user.id, status=status_success,
                               title=message)

        new_channel = ChatChannel.query(new_session, channel_uuid=channel_uuid, user_id=user.id, status=status_success)
        current_channel_index_id = new_channel.id

        ChatMessage.create(new_session, user_id=user.id, channel_id=current_channel_index_id, stream_id=stream_id,
                           question=message)

        response_data = ErrorCode.success({"stream_id": stream_id, "channel_id": channel_uuid})
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"create_stream error:{e}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "server error")


@chat_bp.route('/stream', methods=['GET'])
def stream():
    try:
        stream_id = request.args.get('stream_id')
        session = g.session
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error(f'Invalid token, auth_header:{auth_header}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

        token = auth_header[7:]
        user = User.query(session, token=token)

        if not user:
            logger.error(f'Invalid token, auth_header:{auth_header}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        headers = {
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return Response(generate(stream_id, user.id), headers=headers)
    except Exception as e:
        logger.error(f"stream error:{e}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "server error")

@chat_bp.route('/history/<string:channel_id>', methods=['GET'])
def get_history(channel_id):

    if channel_id is None or channel_id == "":
        logger.error(f'Invalid channel_id, channel_id:{channel_id}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid channel_id')

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

        new_channel = ChatChannel.query(session, channel_uuid=channel_id, user_id=user.id, status=status_success)

        if not new_channel:
            logger.error(f'Invalid channel_id, channel_id:{channel_id}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid channel_id")

        chat_history, e = ChatMessage.query_all(session, limit=100, user_id=user.id, channel_id=new_channel.id)

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
            channels_data.append({"id": channel.id, "channel_id": channel.channel_uuid, "title": channel.title})

        response_data = ErrorCode.success({'channels': channels_data})
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error while getting channels: {str(e)}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Error getting channels")

@chat_bp.route('/channel/<string:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    try:
        if channel_id is None or channel_id == "":
            logger.error(f'Invalid channel_id, channel_id:{channel_id}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid channel_id')

        user = User.query(session, token=token)
        if not user:
            logger.error(f'Invalid token, auth_header:{auth_header}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

        new_channel = ChatChannel.query(session, channel_uuid=channel_id, user_id=user.id, status=status_success)

        if not new_channel:
            logger.error(f'Invalid channel_id, channel_id:{channel_id}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid channel_id")

        success, error = ChatChannel.delete_channel(session, new_channel.id, user.id)
        if success:
            response_data = ErrorCode.success({"message": "Channel deleted successfully"})
            return jsonify(response_data)
        else:
            return error_response(ErrorCode.ERROR_INTERNAL_SERVER, error)

    except Exception as e:
        logger.error(f"Error while deleting channel: {str(e)}")
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Error deleting channel")
