from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate

class ChatManager():
    def __init__(self, api_key, max_length=6):
        self.channels = {}
        self.api_key = api_key
        self.max_length = max_length

    def get_channel(self, channel_id):
        if channel_id not in self.channels:
            self.channels[channel_id] = self.create_llm_chain(self.api_key, self.max_length)
        return self.channels[channel_id]

    @staticmethod
    def create_llm_chain(api_key, max_length=6):
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
        )

        return llm_chain

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


# openai_api = ChatManager(api_key='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')
# print(openai_api.ask('你好,说一个故事吧'))