from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate
import openai

class ChatManager():
    def __init__(self, api_key):
        self.channels = {}
        self.api_key = api_key

    def get_channel(self, channel_id):
        if channel_id not in self.channels:
            self.channels[channel_id] = self.create_llm_chain(self.api_key)
        return self.channels[channel_id]

    @staticmethod
    def create_llm_chain(api_key):
        template = """You are a chatbot having a conversation with a human.

                {chat_history}
                Human: {human_input}
                Chatbot:"""

        prompt = PromptTemplate(
            input_variables=["chat_history", "human_input"],
            template=template
        )
        memory = ConversationBufferMemory(memory_key="chat_history")

        llm_chain = LLMChain(
            llm=OpenAI(openai_api_key=api_key, temperature=0.7),
            prompt=prompt,
            verbose=True,
            memory=memory,
            stream=True,
        )

        return llm_chain

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

    def chat_generator(self, chat_history, message, model="text-davinci-002"):
        openai.api_key = self.api_key
        truncated_chat_history = self.truncate_chat_history(chat_history)
        prompt = f"{truncated_chat_history}The assistant:{message}"

        response = openai.Completion.create(
            engine=model,
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )

        response_text = response.choices[0].text.strip()
        for word in response_text.split():
            print(word)
            yield word

    def ask(self, prompt, conversation_id=None):
        try:
            llm_chain = self.get_channel(conversation_id)
            response = llm_chain.predict(human_input=prompt)

            prompt_with_response = f'Human: {prompt}\nChatbot: {response}'
            consumed_tokens = len(prompt_with_response)

            return response, consumed_tokens * 6, None
        except Exception as e:
            return '', 0, str(e)

    # The following methods are not implemented in ChatManager, but we have to include them as placeholders
    def create_stream(self, prompt, conversation_id=None, version='3.5', system='chatGPT'):
        pass

    def get_stream(self, stream_id):
        pass

    def get_stream_consume(self, stream_id):
        pass


