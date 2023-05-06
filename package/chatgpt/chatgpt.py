import openai

class OpenAIResponse:
    def __init__(self, response_data):
        self.choices = response_data.get('choices', [])
        self.created = response_data.get('created')
        self.id = response_data.get('id')
        self.model = response_data.get('model')
        self.object = response_data.get('object')
        self._parse_choices()

    def _parse_choices(self):
        if self.choices:
            choice = self.choices[0]
            self.finish_reason = choice.get('finish_reason')
            self.index = choice.get('index')
            self.logprobs = choice.get('logprobs')
            self.text = choice.get('text').strip()
        else:
            self.finish_reason = None
            self.index = None
            self.logprobs = None
            self.text = None

class ChatManager():
    def __init__(self, api_key):
        self.api_key = api_key

    def truncate_chat_history(self, chat_history, max_tokens=4096):
        if len(chat_history) > max_tokens:
            tokens_to_remove = len(chat_history) - max_tokens
            removed_dialogue = False
            while not removed_dialogue and tokens_to_remove > 0:
                if chat_history[tokens_to_remove] in ["\n", "\r"]:
                    chat_history = chat_history[tokens_to_remove + 1:]
                    removed_dialogue = True
                else:
                    tokens_to_remove -= 1
        return chat_history

    def ask(self, chat_history, message, model="text-davinci-003"):
        try:
            openai.api_key = self.api_key
            truncated_chat_history = self.truncate_chat_history(chat_history)
            prompt = f"{truncated_chat_history} The assistant:{message}"

            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=2048,
                n=1,
                stop=None,
                temperature=0.6,
                stream=True,
            )

            return response, None
        except Exception as e:
            return '', str(e)

    # The following methods are not implemented in ChatManager, but we have to include them as placeholders
    def create_stream(self, prompt, conversation_id=None, version='3.5', system='chatGPT'):
        pass

    def get_stream(self, stream_id):
        pass

    def get_stream_consume(self, stream_id):
        pass
