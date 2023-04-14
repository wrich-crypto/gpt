
from gevent import monkey
from config.hot_config import *

# Patch the standard library with gevent
monkey.patch_all()
from flask import Flask, Response
import requests
app = Flask(__name__)

from package.chatgpt.uchatgpt import *

def test_chat_api(access_token):
    chat_api = ChatAPI(access_token)

    # # Test ask() method
    # try:
    #     response = chat_api.ask("猫有多少种？")
    #     print(response)
    # except Exception as e:
    #     print(f"Test failed: {e}")

    # Test create_stream() and get_stream() methods
    try:
        create_stream_response = chat_api.create_stream("猫有多少种？")
        print(create_stream_response)

        stream_id = create_stream_response["data"]["streamId"]
        stream_response = chat_api.get_stream(stream_id)
        print(stream_response.text)
    except Exception as e:
        print(f"Test failed: {e}")

# if __name__ == "__main__":
#     test_chat_api()

# Replace this URL with the third-party API URL you want to stream data from
THIRD_PARTY_API_URL = "https://your-third-party-api-url/stream"

def create_stream_with_retry(message, channel=None, max_attempts=None):
    if max_attempts is None:
        max_attempts = len(hot_config.token_cycle)

    for _ in range(max_attempts):
        access_token = hot_config.get_next_api_key()

        if access_token is None or access_token.strip() == '':
            break

        chat_api = ChatAPI(access_token)

        channel_id = channel if channel and channel.strip() != "" else generate_uuid()
        create_stream_response = chat_api.create_stream(message, channel_id)

        if create_stream_response and str(create_stream_response["code"]) == '0':
            stream_id = create_stream_response["data"]["streamId"]
            return chat_api.get_stream(stream_id)
        else:
            hot_config.remove_api_key(access_token)

    raise ValueError("Failed to create stream after maximum attempts.")

@app.route('/stream')
def stream():
    message = '用一句话概括猫咪'
    def generate():
        stream_response = create_stream_with_retry(message, max_attempts=3)

        content = ''
        for chunk in stream_response.iter_content(chunk_size=1024):
            if chunk:
                decoded_chunk = chunk.decode("utf-8")
                decoded_chunk_obj = DecodedChunk(decoded_chunk)

                if decoded_chunk_obj.event == 'message':
                    content = content + decoded_chunk_obj.data
                print(content)
                yield decoded_chunk

    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run()
