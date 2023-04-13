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
                   "sceneId": 101,
                   "accessToken": self.access_token}
        response = requests.post(url, json=payload)
        return response.json()

    def create_stream(self, prompt, conversation_id=None):
        url = f"{self.base_url}/chat/stream/create"
        payload = {"prompt": prompt,
                   "conversationId": conversation_id,
                   "sceneId": 101,
                   "accessToken": self.access_token}
        response = requests.post(url, json=payload)
        return response.json()

    def get_stream(self, stream_id):
        url = f"{self.base_url}/chat/stream?streamId={stream_id}&accessToken={self.access_token}"
        response = requests.get(url, stream=True)
        return response

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