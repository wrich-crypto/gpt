from .chat_routes import *
from package.chatgpt.uchatgpt import *
from .chat_module import *
from ..user.user_module import *
import json
from flask import Flask, request, Response, stream_with_context
from src.admin.admin_module import ApiKeys

def create_stream_with_retry(message, channel=None, version='3.5', system='chatGPT', max_attempts=3):
    for _ in range(max_attempts):
        if version == '3.5' or version == '4':
            #
            channel_id = channel if channel and channel.strip() != "" else generate_uuid()
            stream_id = generate_uuid()
            return stream_id, channel_id

        access_token = hot_config.get_next_api_key()
        logger.info(access_token)

        if system is None:
            system = 'chatGPT'

        if access_token is None or access_token.strip() == '':
            break

        chat_api = ChatAPI(access_token)

        channel_id = channel if channel and channel.strip() != "" else generate_uuid()
        create_stream_response = chat_api.create_stream(message, channel_id, version, system)

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
def generate(session, stream_id, user_id):
    try:
        chatMessage_instance = ChatMessage.query(session, stream_id=stream_id)
        history_content = ''

        supplier = DevConfig.get_supplier(session)

        if chatMessage_instance is not None and chatMessage_instance.version is not None:
            model_type = DevConfig.get_model_type_by_version(chatMessage_instance.version)
        else:
            model_type = '3.5'

        access_token = ApiKeys.get_random_key(session, supplier=supplier, model_type=model_type)
        print(access_token)
        #使用官方的openai库
        if supplier == SUPPLIER_TYPE_OPENAI and chatMessage_instance is not None and chatMessage_instance.version is not None\
                and (chatMessage_instance.version == '3.5' or chatMessage_instance.version == '4'):
            openai_model = get_model(chatMessage_instance.version)
            openai_api = OpenAIChat(access_token, openai_model)

            #获取历史数据
            # chat_history_list = ChatMessage.get_message_history_by_channel_id(session, chatMessage_instance.channel_id)
            limit_num = 2 if chatMessage_instance.using_context == using_context_open else 1
            chat_history_list, e = ChatMessage.query_all(session, limit=limit_num, desc=True, channel_id=chatMessage_instance.channel_id)

            if e is not None:
                logger.info(e)

            chat_history_list = list(reversed(chat_history_list))

            for chat_history in chat_history_list:
                if chat_history.question and chat_history.question != '':
                    history_content = history_content + chat_history.question
                    openai_api.add_message("user", chat_history.question)

                if chat_history.answer and chat_history.answer != '':
                    history_content = history_content + chat_history.answer
                    openai_api.add_message("system", chat_history.answer)

            response, error_msg = openai_api.generate_chat_response()

            if error_msg is not None:
                logger.error(f'error_msg:{error_msg}')

            content = ''
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    decoded_chunk = chunk.decode("utf-8")

                    chunk_obj = DecodedOpenaiChunk(decoded_chunk)

                    if chunk_obj and chunk_obj.data:
                        event_name = 'message'
                        markdown_data = chunk_obj.data.replace('\\n', '<c-api-line>')   #适配uchat格式
                        formatted_chunk = f"id: {chunk_obj.id}\nevent: {event_name}\ndata: {markdown_data}\n\n"
                        content = content + chunk_obj.data.replace('\\n', '\n')
                        yield formatted_chunk

            openai_api.add_message("system", content)

            consume_token_amount = num_tokens_from_messages(openai_api.messages, openai_model)
            consume_token_amount = consume_token_amount * 50 if chatMessage_instance.version == '4' else (consume_token_amount * 2.5 * 3 / 4)
            print(f'consume token:{consume_token_amount}')
        #使用uchat
        elif supplier == SUPPLIER_TYPE_UCHAT:
            # access_token = hot_config.get_next_api_key()

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

            consume_token_amount, error_message, get_stream_consume_response = chat_api.get_stream_consume(stream_id)
            logger.info(f'consume_token_amount:{consume_token_amount}, error_message:{error_message}, '
                        f'get_stream_consume_response:{get_stream_consume_response}')
        else:
            logger.error(f'supplier error: {supplier}')
            yield f"data: {json.dumps(error_response(ErrorCode.ERROR_INTERNAL_SERVER, 'Internal server error'))}\n\n"

        logger.debug(content)
        new_session = session_factory()

        chat_message = ChatMessage.query(new_session, stream_id=stream_id)
        if chat_message:
            success, error_message = ChatMessage.update(new_session, {"stream_id": stream_id},
                                                 {"answer": content, "tokens_consumed": consume_token_amount,
                                                  "api_key": access_token})
            if error_message:
                logger.info(f'generate ChatMessage.update stream_id:{stream_id} error:{error_message} success:{success}')
            else:
                logger.info(f'generate ChatMessage.update stream_id:{stream_id} success:{success}')

        if consume_token_amount >= 0:

            if update_user_consumed(new_session, user_id, consume_token_amount) is False:
                logger.error(f'generate - update_user_consumed user_id:{user_id} consume_token_amount : '
                             f'{consume_token_amount} error')
            else:
                logger.info(f'generate - update_user_consumed user_id:{user_id} consume_token_amount : '
                            f'{consume_token_amount} success')

        update_api_key_tokens(new_session, api_key=access_token)
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
        using_context = data.get('using_context')
        system = 'chatGPT'

        if balance_valid(new_session, user.id) is False:
            logger.error(f'Insufficient balance, auth_header:{auth_header}, user id:{user.id}')
            return error_response(ErrorCode.ERROR_BALANCE, "Insufficient balance")

        stream_id, channel_uuid = create_stream_with_retry(message, channel_uuid, str(version), system=system)

        if not ChatChannel.exists(new_session, channel_uuid=channel_uuid, user_id=user.id, status=status_success):
            _, e = ChatChannel.create(new_session, channel_uuid=channel_uuid, user_id=user.id, status=status_success,
                               title=message, version=version)

            if e is not None:
                logger.error(f'create_stream ChatChannel.create error:{e}')

        new_channel = ChatChannel.query(new_session, channel_uuid=channel_uuid, user_id=user.id, status=status_success)
        current_channel_index_id = new_channel.id

        using_context_status = using_context_open if using_context is True else using_context_stop
        print(f'using_context:{using_context} using_context_status:{using_context_status}')
        ChatMessage.create(new_session, user_id=user.id, channel_id=current_channel_index_id, stream_id=stream_id,
                           question=message, version=version, using_context=using_context_status)

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
            return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

        headers = {
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return Response(generate(session, stream_id, user.id), headers=headers)
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
            return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

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
            return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

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
            return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

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
