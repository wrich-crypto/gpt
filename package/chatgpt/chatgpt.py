import requests
from typing import List, Dict, Union
import uuid
import json
import re

model3_5 = 'gpt-3.5-turbo'
model_4 = 'gpt-4'

def get_model(version='3.5'):
    if version == '4':
        return  model_4
    else:
        return model3_5

class OpenAIChat:

    def __init__(self, api_key: str, model=model3_5):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def generate_chat_response(self, temperature: float = 0.6,
                               top_p: float = 1, n: int = 1, stop: Union[str, List[str]] = None,
                               max_tokens: int = 2048, presence_penalty: float = 0, frequency_penalty: float = 0,
                               logit_bias: Dict[str, float] = None, user: str = None):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": self.model,
                "messages": self.messages,
                "temperature": temperature,
                "top_p": top_p,
                "n": n,
                "stream": True,
            }
            if stop is not None:
                data["stop"] = stop
            if max_tokens is not None:
                data["max_tokens"] = max_tokens
            if presence_penalty != 0:
                data["presence_penalty"] = presence_penalty
            if frequency_penalty != 0:
                data["frequency_penalty"] = frequency_penalty
            if logit_bias is not None:
                data["logit_bias"] = logit_bias
            if user is not None:
                data["user"] = user

            response = requests.post(self.base_url, json=data, headers=headers, stream=True)
            return response, None
        except Exception as e:
            return None, e

# class DecodedOpenaiChunk:
#     def __init__(self, chunk: str):
#         self.id = str(uuid.uuid4())
#         self.event = 'message'
#         self.data = None
#
#         self._parse_chunk(chunk)
#
#     def _parse_chunk(self, chunk: str):
#         try:
#             json_str = chunk.lstrip('data: ')
#             json_data = json.loads(json_str)
#             delta = json_data.get('choices', [{}])[0].get('delta', {})
#             if 'role' in delta:
#                 self.data = delta.get('content', '')
#             else:
#                 self.data = delta.get('content', '')
#
#             self.data = self.data.replace('\n', '\\n')
#         except json.JSONDecodeError as e:
#             print(f"Error parsing chunk: {e}")

class DecodedOpenaiChunk:
    def __init__(self, chunk: str):
        self.id = str(uuid.uuid4())
        self.event = 'message'
        self.data = ''

        self._parse_chunk(chunk)

    def _parse_chunk(self, chunk: str):
        try:
            # 使用'data: '作为分隔符分割字符串
            parts = chunk.split('data: ')

            # 删除每个部分前面的空白字符，并且跳过第一部分（因为它在分割后是一个空字符串）
            json_parts = [part.strip() for part in parts if part]

            for json_str in json_parts:
            # json_str = chunk.lstrip('data: ')
                print(json_str)
                json_data = json.loads(json_str)
                print(f'json_data:{json_data}')
                choices = json_data.get('choices', [{}])
                print(f'choices:{choices}')
                for choice in choices:
                    delta_content = choice.get('delta', {}).get('content', '')
                    if delta_content:
                        self.data += delta_content
            self.data = self.data.replace('\n', '\\n')
        except json.JSONDecodeError as e:
            print(f"Error parsing chunk: {e}")