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

class DecodedOpenaiChunk:
    def __init__(self, chunk: str):
        self.id = str(uuid.uuid4())
        self.event = 'message'
        self.data = None

        self._parse_chunk(chunk)

    def _parse_chunk(self, chunk: str):
        data_match = re.search(r'content":\s*"((?:(?!"},"index").)+)', chunk)
        if data_match:
            self.data = data_match.group(1)

    # def _parse_chunk(self, input_string):
    #     # 去除字符串前面的 "data: "
    #     try:
    #         input_string = input_string.replace("data: ", "", 1)
    #
    #         # 将字符串解析为 Python 对象（字典）
    #         obj = json.loads(input_string)
    #
    #         # 提取 id 和 data 的值
    #         result_id = obj['id']
    #         data_content = obj['choices'][0]['delta']['content']
    #
    #         self.id = result_id
    #         self.data = data_content
    #     except Exception as e:
    #         print(e)