import requests
import re
import uuid

def generate_uuid():
    # Generate a random UUID
    uuid4 = uuid.uuid4()
    return str(uuid4)

class ChatAPI:
    def __init__(self, access_token, base_url="https://api.chatuapi.com"):
        self.access_token = access_token
        self.base_url = base_url

    def ask(self, prompt, conversation_id=None):
        url = f"{self.base_url}/chat/ask"
        payload = {"prompt": prompt,
                   "conversationId": conversation_id,
                   "accessToken": self.access_token}
        response = requests.post(url, json=payload)
        return response.json()

    def create_stream(self, prompt, conversation_id=None, version='3.5', system=''):
        url = f"{self.base_url}/chat/stream/create"

        payload = {"prompt": prompt,
                   "conversationId": conversation_id,
                   "accessToken": self.access_token,
                   "useEscape": True}

        if version == '4':
            payload['sceneId'] = 101

        if system != '':
            payload['system'] = system

        response = requests.post(url, json=payload)
        return response.json()

    def get_stream(self, stream_id):
        url = f"{self.base_url}/chat/stream?streamId={stream_id}&accessToken={self.access_token}"
        response = requests.get(url, stream=True)
        return response

    def get_stream_consume(self, stream_id):
        consume_response = ''
        try:
            url = f"{self.base_url}/chat/stream/sync"
            payload = {"streamId": stream_id,
                       "accessToken": self.access_token}
            response = requests.post(url, json=payload)

            if response.status_code != 200:
                print(f"Unexpected HTTP status code: {response.status_code}")
                print(f"Response content: {response.content}")
                return 500, "Unexpected HTTP status code", None

            consume_response = response.json()
            print(f'get_stream_consume response:{response}')

            if consume_response and str(consume_response["code"]) == 0:
                consume_token_amount = int(consume_response["data"]["token"])
            else:
                consume_token_amount = 500

            return consume_token_amount, None, consume_response
        except Exception as e:
            return 500, e, consume_response

class DecodedChunk:
    def __init__(self, chunk: str):
        self.id = None
        self.event = None
        self.data = None

        self._parse_chunk(chunk)

    def _parse_chunk(self, chunk: str):
        # 匹配 id
        id_match = re.search(r'id:\s*(\S+)', chunk)
        if id_match:
            self.id = id_match.group(1)

        # 匹配 event
        event_match = re.search(r'event:\s*(\S+)', chunk)
        if event_match:
            self.event = event_match.group(1)

        # 匹配 data
        data_match = re.search(r'data:\s*(.+)', chunk)
        if data_match:
            self.data = data_match.group(1)